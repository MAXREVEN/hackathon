import os
import sys
import tempfile
from pathlib import Path

# Must run BEFORE the app is imported: use a throw-away database and a test secret.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_tmp) / 'test.db').as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-test-secret-test-secret-123"
os.environ["LOST_ENV"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import itertools
import pytest
from fastapi.testclient import TestClient

from app.main import app

_n = itertools.count(1)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def user(client):
    """A signed-in client (cookie stored by the TestClient)."""
    r = client.post("/api/auth/signup", json={"name": "Sara", "email": f"sara{next(_n)}@example.com",
                                              "password": "supersecret1"})
    assert r.status_code == 200, r.text
    return client
