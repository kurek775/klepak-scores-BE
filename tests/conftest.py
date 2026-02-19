"""
Shared pytest fixtures.

Uses an in-memory SQLite engine so tests have no dependency on PostgreSQL.
The `get_session` dependency is overridden in the FastAPI app for every test.
"""

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch

from app.database import get_session
from app.main import app
from app.core.limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the shared in-memory rate limiter before each test.

    Without this, sequential tests that call /auth/register or /auth/login
    exhaust the per-IP counters (5/min, 10/min) and start returning 429s.
    """
    limiter._storage.reset()
    yield


@pytest.fixture(name="engine", scope="function")
def engine_fixture():
    """Fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client", scope="function")
def client_fixture(engine):
    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    # Patch init_db so the lifespan doesn't try to connect to PostgreSQL.
    # The SQLite tables are already created by the engine fixture.
    with patch("app.main.init_db"):
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client
    app.dependency_overrides.clear()


# ── Auth helpers ────────────────────────────────────────────────────────────

def register_and_login(client: TestClient, email: str, password: str, full_name: str) -> str:
    """Register a user and return the JWT access token."""
    client.post("/auth/register", json={"email": email, "password": password, "full_name": full_name})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


@pytest.fixture(name="admin_token")
def admin_token_fixture(client):
    """First registered user automatically becomes admin."""
    return register_and_login(client, "admin@test.com", "Password1!", "Admin User")


@pytest.fixture(name="evaluator_token")
def evaluator_token_fixture(client, admin_token, engine):
    """Register a second user (evaluator), activate them via DB, then log in."""
    from app.models.user import User
    from sqlmodel import select

    client.post(
        "/auth/register",
        json={"email": "eval@test.com", "password": "Password1!", "full_name": "Eval User"},
    )
    # Activate via direct DB manipulation (admin would normally do this via /admin)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "eval@test.com")).first()
        if user:
            user.is_active = True
            session.add(user)
            session.commit()

    resp = client.post("/auth/login", json={"email": "eval@test.com", "password": "Password1!"})
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
