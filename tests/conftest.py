"""Sign-in for tests (P-20). Every /api route needs a token, so tests act as a demo account:

    client = signed_in()                    # the bid manager
    client.post(url, headers=auth("crown.de"))   # one request as someone else (Bearer wins over the default)

The app is imported inside the helpers: each test module sets STORE_DIR before its own import of the app.
"""
import functools
import os

import pytest

os.environ["DEMO_PASSWORD"] = "test-password"  # tests never depend on the local .env
os.environ["MYSQL_HOST"] = ""                    # accounts go in the test store's SQLite, never the local MySQL
os.environ["CATALOG_REFRESH_HOURS"] = "0"        # no network in tests (P-34)


@pytest.fixture(autouse=True, scope="session")
def draft_stage():
    """Tests written before C-27 build bids by reading the same sample RFP and reviewing the draft; switch the
    automatic freeze and the read-once rule off for the whole run (session scope: module fixtures need it too).
    tests/test_p32_auto_freeze.py switches both on again for its own test (monkeypatch restores them)."""
    from app.modules.opportunities import service as opportunities
    from app.modules.requirements import service as requirements
    requirements.FREEZE_ON_READ, opportunities.READ_ONCE = False, False


@functools.cache   # one sign-in per account: checking a password takes about 0.4 s by design
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
