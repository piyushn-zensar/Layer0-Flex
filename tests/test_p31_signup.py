"""P-31 (C-26): sign-up with a chosen role (never administrator), unique usernames and display names, an attempt
limit; a signed-up unit manager can do the unit's work; every API route needs a session and the administrator can
complete no write."""
import os
import re
import tempfile

os.environ["STORE_DIR"] = tempfile.mkdtemp()

from conftest import auth, signed_in  # noqa: E402


def _signup(client, **body):
    base = {"username": "new.pm", "name": "Nadia Crown", "password": "long-enough-1", "role": "product_manager", "bu": "CROWN"}
    return client.post("/api/auth/signup", json=base | body)


def test_signup_rules_and_unit_work():
    from fastapi.testclient import TestClient

    from app.core import auth as core_auth
    from app.main import app
    from scripts import seed_demo

    anon = TestClient(app)
    options = anon.get("/api/auth/signup-options").json()
    assert "admin" not in options["roles"] and "CROWN" in options["units"]
    assert _signup(anon, role="admin").status_code == 422                       # never administrator
    assert _signup(anon, bu=None).status_code == 422                            # a unit role needs a unit
    assert _signup(anon, password="short").status_code == 422
    assert _signup(anon, username="bid.manager").status_code == 409             # roster names are reserved
    assert _signup(anon, name="crown product manager").status_code == 409       # display names are unique
    r = _signup(anon)
    assert r.status_code == 200 and r.json()["user"]["role"] == "product_manager" and anon.cookies.get(core_auth.COOKIE)
    me = anon.get("/api/auth/me").json()
    assert (me["name"], me["bu"], me["role_label"]) == ("Nadia Crown", "CROWN", "Unit manager")
    assert _signup(anon).status_code == 409                                     # username taken
    bm = TestClient(app).post("/api/auth/signup", json={"username": "new.bm", "name": "Bea Bids", "password": "long-enough-2",
                                                        "role": "bid_manager", "bu": "CROWN"}).json()["user"]
    assert bm["bu"] is None                                                      # the bid manager has no unit

    # a signed-up unit manager validates the unit's answers (names come from accounts, not only the unit file)
    seed_demo.main()
    client = signed_in()
    opp = client.get("/api/portfolio").json()[0]["opp"]["id"]
    item = next(i for i in client.get("/api/inbox/CROWN").json()["items"] if i["opportunity_id"] == opp and i["status"] == "assigned")
    url = f"/api/assignments/{item['id']}"
    assert client.post(f"{url}/respond", json={"compliance": "met"}, headers=auth("crown.de")).status_code == 200
    nadia = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.post(f"{url}/validate", json={"ok": True}, headers=nadia).status_code == 200

    # attempt limit: five failed sign-ins lock the username for five minutes
    for _ in range(5):
        assert anon.post("/api/auth/login", json={"username": "new.pm", "password": "wrong-password"}).status_code == 401
    assert anon.post("/api/auth/login", json={"username": "new.pm", "password": "long-enough-1"}).status_code == 429
    core_auth._attempts.clear()


def test_every_route_needs_a_session_and_admin_writes_nothing():
    from fastapi.testclient import TestClient

    from app.main import app
    anon, admin = TestClient(app), signed_in("admin")
    filled = lambda path: re.sub(r"\{[^}]+\}", "1", path.replace("{opp_id}", "OPP-0001").replace("{bu}", "CROWN"))
    checked = 0
    for path, ops in app.openapi()["paths"].items():
        if not path.startswith("/api/") or path.startswith("/api/auth/") or path == "/api/catalog/refresh":  # the administrator may refresh the published catalog (an operations task; it would also go online)
            continue
        for method in (m.upper() for m in ops):
            url = filled(path)
            assert anon.request(method, url).status_code == 401, (method, path)
            if method != "GET":
                status = admin.request(method, url, json={}).status_code
                assert not 200 <= status < 300, (method, path, status)  # the administrator only reads
            checked += 1
    assert checked > 60, checked
