"""Tests for forgot-password / reset-password flow."""

import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from tests.conftest import auth_headers, register_and_login


def _get_raw_token(engine) -> str:
    """Retrieve the raw token from the DB by looking at the most recent PasswordResetToken."""
    from app.models.password_reset_token import PasswordResetToken

    with Session(engine) as session:
        token = session.exec(
            select(PasswordResetToken).order_by(PasswordResetToken.id.desc())
        ).first()
        return token.token_hash if token else ""


def _request_reset(client: TestClient, email: str):
    return client.post("/auth/forgot-password", json={"email": email})


# ── Forgot password ─────────────────────────────────────────────────────────

def test_forgot_password_existing_user(client: TestClient, admin_token: str):
    """Requesting reset for existing email returns success (no leak)."""
    resp = _request_reset(client, "admin@test.com")
    assert resp.status_code == 200
    assert "reset link" in resp.json()["detail"].lower() or "email" in resp.json()["detail"].lower()


def test_forgot_password_unknown_email(client: TestClient):
    """Requesting reset for unknown email still returns success (no leak)."""
    resp = _request_reset(client, "nobody@test.com")
    assert resp.status_code == 200


def test_forgot_password_creates_token(client: TestClient, admin_token: str, engine):
    """A PasswordResetToken is created in the database."""
    from app.models.password_reset_token import PasswordResetToken

    _request_reset(client, "admin@test.com")
    with Session(engine) as session:
        tokens = session.exec(select(PasswordResetToken)).all()
        assert len(tokens) >= 1


def test_forgot_password_invalidates_old_tokens(client: TestClient, admin_token: str, engine):
    """Requesting a second reset marks the first token as used."""
    from app.models.password_reset_token import PasswordResetToken

    _request_reset(client, "admin@test.com")
    _request_reset(client, "admin@test.com")

    with Session(engine) as session:
        tokens = session.exec(
            select(PasswordResetToken).order_by(PasswordResetToken.id)
        ).all()
        # First token should be marked used, second should not be
        assert tokens[0].used is True
        assert tokens[1].used is False


# ── Reset password ──────────────────────────────────────────────────────────

def test_reset_password_success(client: TestClient, admin_token: str, engine):
    """User can reset password with a valid token."""
    from app.models.password_reset_token import PasswordResetToken

    _request_reset(client, "admin@test.com")

    # Create a known token directly so we have the raw value.
    import secrets
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    from app.models.user import User
    from datetime import datetime, timedelta

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        # Mark all existing tokens as used
        existing = session.exec(select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)).all()
        for t in existing:
            t.used = True
            session.add(t)
        # Create a fresh token we know the raw value of (naive datetime for SQLite)
        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        session.add(reset_token)
        session.commit()

    resp = client.post("/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewPassword1!",
    })
    assert resp.status_code == 200

    # Verify new password works
    login_resp = client.post("/auth/login", json={"email": "admin@test.com", "password": "NewPassword1!"})
    assert login_resp.status_code == 200


def test_reset_password_invalid_token(client: TestClient):
    resp = client.post("/auth/reset-password", json={
        "token": "totally-invalid-token",
        "new_password": "NewPassword1!",
    })
    assert resp.status_code == 400


def test_reset_password_expired_token(client: TestClient, admin_token: str, engine):
    """Expired tokens are rejected."""
    import secrets
    from datetime import datetime, timedelta
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash,
            expires_at=datetime.utcnow() - timedelta(minutes=1),  # Already expired
        )
        session.add(reset_token)
        session.commit()

    resp = client.post("/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewPassword1!",
    })
    assert resp.status_code == 400


def test_reset_password_reuse_token(client: TestClient, admin_token: str, engine):
    """Used tokens are rejected on second use."""
    import secrets
    from datetime import datetime, timedelta
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        session.add(reset_token)
        session.commit()

    # First reset succeeds
    resp1 = client.post("/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewPassword1!",
    })
    assert resp1.status_code == 200

    # Second reset with same token fails
    resp2 = client.post("/auth/reset-password", json={
        "token": raw_token,
        "new_password": "AnotherPass1!",
    })
    assert resp2.status_code == 400


def test_reset_password_weak_password_422(client: TestClient, admin_token: str, engine):
    """Weak password is rejected by schema validation."""
    import secrets
    from datetime import datetime, timedelta
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        session.add(reset_token)
        session.commit()

    resp = client.post("/auth/reset-password", json={
        "token": raw_token,
        "new_password": "weak",
    })
    assert resp.status_code == 422
