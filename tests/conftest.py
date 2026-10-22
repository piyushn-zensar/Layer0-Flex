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
os.environ["LLM_PROVIDER"] = "mock"              # frozen answers only: a cache miss never calls the model


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


# P-32 (C-27). The tests read the same sample RFPs into many bids of one store. The known-instance lookup would send
# every later upload of a file to the first bid that holds it, so it is off unless a test is marked known_instances.
import pytest  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "known_instances: keep P-32's known-instance lookup on for this test")


_LOOKUP = {"on": False}


@pytest.fixture(autouse=True, scope="session")
def _one_rfp_many_bids():
    """Session-wide, so module-scoped fixtures that create bids see it too; the marker turns the lookup on per test."""
    from app.modules.opportunities import service
    real = service.known
    service.known = lambda *args, **kwargs: real(*args, **kwargs) if _LOOKUP["on"] else None
    yield
    service.known = real


@pytest.fixture(autouse=True)
def _known_instances_marker(request):
    _LOOKUP["on"] = "known_instances" in request.keywords
    yield
    _LOOKUP["on"] = False


@pytest.fixture
def incomplete_read(monkeypatch):
    """The read counts as incomplete, so extract leaves the register unfrozen: the working-register actions (edit,
    split, merge, add, exclude before a baseline exists) are reachable as after a real incomplete read (P-32)."""
    from app.modules.requirements import service
    monkeypatch.setattr(service, "read_complete", lambda coverage: False)


def freeze(opp: str):
    """Freeze a register the way the seed does (P-32 removed the publish route; a complete read freezes by itself)."""
    from app.core.db import SessionLocal
    from app.modules.requirements import service
    with SessionLocal() as db:
        b = service.freeze(db, opp, "Bid Manager")
        return {"number": b.number, "count": b.count}
