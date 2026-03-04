"""Tests for invitation validation and acceptance flow."""

import hashlib
import secrets
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from tests.conftest import auth_headers


def _create_invitation_token(engine, email: str, role: str = "EVALUATOR", expired: bool = False) -> str:
    """Create an invitation token directly in the DB and return the raw token.

    Uses naive datetimes (no timezone) because SQLite stores datetimes without tz info,
    and the service layer comparisons use datetime.now(timezone.utc) which is effectively
    the same as datetime.utcnow() when stored in SQLite.
    """
    from app.models.invitation_token import InvitationToken

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = (
        datetime.utcnow() - timedelta(days=1) if expired
        else datetime.utcnow() + timedelta(days=7)
    )

    with Session(engine) as session:
        inv = InvitationToken(
            email=email, role=role, token_hash=token_hash,
            expires_at=expires_at, invited_by=1,
        )
        session.add(inv)
        session.commit()

    return raw_token


# ── Validate invitation ────────────────────────────────────────────────────

def test_validate_invitation_valid(client: TestClient, admin_token: str, engine):
    raw_token = _create_invitation_token(engine, "new_eval@test.com")
    resp = client.get(f"/auth/validate-invitation?token={raw_token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "new_eval@test.com"
    assert data["role"] == "EVALUATOR"


def test_validate_invitation_invalid_token(client: TestClient):
    resp = client.get("/auth/validate-invitation?token=bogus-token")
    assert resp.status_code == 400


def test_validate_invitation_expired(client: TestClient, admin_token: str, engine):
    raw_token = _create_invitation_token(engine, "expired@test.com", expired=True)
    resp = client.get(f"/auth/validate-invitation?token={raw_token}")
    assert resp.status_code == 400


# ── Accept invitation ──────────────────────────────────────────────────────

def test_accept_invitation_success(client: TestClient, admin_token: str, engine):
    raw_token = _create_invitation_token(engine, "accept@test.com")
    resp = client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "Accepted User",
        "password": "Password1!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Verify user can log in
    login_resp = client.post("/auth/login", json={"email": "accept@test.com", "password": "Password1!"})
    assert login_resp.status_code == 200


def test_accept_invitation_creates_correct_role(client: TestClient, admin_token: str, engine):
    raw_token = _create_invitation_token(engine, "eval_role@test.com", role="EVALUATOR")
    resp = client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "Eval Role User",
        "password": "Password1!",
    })
    token = resp.json()["access_token"]
    me = client.get("/auth/me", headers=auth_headers(token)).json()
    assert me["role"] == "EVALUATOR"
    assert me["is_active"] is True


def test_accept_invitation_duplicate_email_409(client: TestClient, admin_token: str, engine):
    """Cannot accept invitation if email is already registered."""
    raw_token = _create_invitation_token(engine, "admin@test.com")  # admin already registered
    resp = client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "Duplicate",
        "password": "Password1!",
    })
    assert resp.status_code == 409


def test_accept_invitation_invalid_token(client: TestClient):
    resp = client.post("/auth/accept-invitation", json={
        "token": "bad-token",
        "full_name": "Nobody",
        "password": "Password1!",
    })
    assert resp.status_code == 400


def test_accept_invitation_expired_token(client: TestClient, admin_token: str, engine):
    raw_token = _create_invitation_token(engine, "expired_accept@test.com", expired=True)
    resp = client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "Expired",
        "password": "Password1!",
    })
    assert resp.status_code == 400


def test_accept_invitation_weak_password_422(client: TestClient, admin_token: str, engine):
    raw_token = _create_invitation_token(engine, "weak_pw@test.com")
    resp = client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "Weak",
        "password": "short",
    })
    assert resp.status_code == 422


def test_accept_invitation_token_marked_used(client: TestClient, admin_token: str, engine):
    """After acceptance, token cannot be reused."""
    raw_token = _create_invitation_token(engine, "onetime@test.com")
    client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "One Time",
        "password": "Password1!",
    })
    # Second attempt fails
    resp = client.post("/auth/accept-invitation", json={
        "token": raw_token,
        "full_name": "Again",
        "password": "Password1!",
    })
    assert resp.status_code == 400
