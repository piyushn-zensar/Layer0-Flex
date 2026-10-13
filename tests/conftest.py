"""Sign-in for tests (P-20). Every /api route needs a token, so tests act as a demo account:

    client = signed_in()                    # the bid manager
    client.post(url, headers=auth("crown.de"))   # one request as someone else (Bearer wins over the default)

The app is imported inside the helpers: each test module sets STORE_DIR before its own import of the app.
"""
import os

os.environ["DEMO_PASSWORD"] = "test-password"  # tests never depend on the local .env


def auth(username: str = "bid.manager") -> dict:
    """Headers that sign the request in as `username`, through the real login route."""
    from fastapi.testclient import TestClient

    from app.main import app
    r = TestClient(app).post("/api/auth/login", json={"username": username, "password": "test-password"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def signed_in(username: str = "bid.manager"):
    """A test client whose requests are signed in as `username` (no cookies are kept between helpers)."""
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app, headers=auth(username))
