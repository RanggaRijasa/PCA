from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import admin as admin_api
from backend.api import auth as auth_api
from backend.api import chat as chat_api
import backend.auth.session as session_module
from backend.db.connection import get_connection, transaction
from backend.db.schema import initialize_database
from backend.db.users import seed_default_roles_and_users
from backend.main import app


TEST_PASSWORD = "Local-Test-Password-123!"


@pytest.fixture
def auth_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "auth.db"
    initialize_database(path)
    with transaction(path) as connection:
        seed_default_roles_and_users(connection, TEST_PASSWORD)

    monkeypatch.setattr(session_module, "get_connection", lambda: get_connection(path))
    monkeypatch.setattr(auth_api, "transaction", lambda: transaction(path))
    monkeypatch.setattr(chat_api, "transaction", lambda: transaction(path))
    monkeypatch.setattr(chat_api, "get_connection", lambda: get_connection(path))
    monkeypatch.setattr(admin_api, "get_connection", lambda: get_connection(path))
    return path


@pytest.fixture
def api_client(auth_database: Path) -> TestClient:
    del auth_database
    with TestClient(app) as client:
        yield client


def login(client: TestClient, username: str = "admin") -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
