"""Tests for /admin endpoints — user CRUD, invitations."""

import io

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from tests.conftest import auth_headers, register_and_login


def _make_super_admin(engine, email: str):
    """Promote a user to SUPER_ADMIN via DB."""
    from app.models.user import User, UserRole

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        user.role = UserRole.SUPER_ADMIN
        session.add(user)
        session.commit()


# ── List users ──────────────────────────────────────────────────────────────

def test_list_users(client: TestClient, admin_token: str):
    resp = client.get("/admin/users", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 1
    assert users[0]["email"] == "admin@test.com"


def test_list_users_non_admin_403(client: TestClient, evaluator_token: str):
    resp = client.get("/admin/users", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403


def test_list_users_pagination(client: TestClient, admin_token: str, evaluator_token: str):
    resp = client.get("/admin/users?skip=0&limit=1", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ── Update user ─────────────────────────────────────────────────────────────

def test_update_user_role(client: TestClient, admin_token: str, evaluator_token: str, engine):
    """Super admin can change a user's role."""
    _make_super_admin(engine, "admin@test.com")
    # Re-login to get fresh token with super admin context
    sa_token = register_and_login(client, "sa@test.com", "Password1!", "SA", engine)
    _make_super_admin(engine, "sa@test.com")
    sa_token2 = client.post("/auth/login", json={"email": "sa@test.com", "password": "Password1!"}).json()["access_token"]

    eval_user = client.get("/auth/me", headers=auth_headers(evaluator_token)).json()
    resp = client.patch(
        f"/admin/users/{eval_user['id']}",
        headers=auth_headers(sa_token2),
        json={"role": "ADMIN"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMIN"


def test_update_user_activate(client: TestClient, admin_token: str, engine):
    """Super admin can activate/deactivate users."""
    _make_super_admin(engine, "admin@test.com")
    sa_token = client.post("/auth/login", json={"email": "admin@test.com", "password": "Password1!"}).json()["access_token"]

    # Register a new inactive user
    client.post("/auth/register", json={"email": "new@test.com", "password": "Password1!", "full_name": "New"})
    from app.models.user import User
    with Session(engine) as session:
        new_user = session.exec(select(User).where(User.email == "new@test.com")).first()
        user_id = new_user.id

    resp = client.patch(
        f"/admin/users/{user_id}",
        headers=auth_headers(sa_token),
        json={"is_active": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


def test_update_user_non_super_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    """Regular admin cannot update users (requires super admin)."""
    eval_user = client.get("/auth/me", headers=auth_headers(evaluator_token)).json()
    resp = client.patch(
        f"/admin/users/{eval_user['id']}",
        headers=auth_headers(admin_token),
        json={"role": "ADMIN"},
    )
    assert resp.status_code == 403


def test_cannot_assign_super_admin_role(client: TestClient, admin_token: str, evaluator_token: str, engine):
    _make_super_admin(engine, "admin@test.com")
    sa_token = client.post("/auth/login", json={"email": "admin@test.com", "password": "Password1!"}).json()["access_token"]
    eval_user = client.get("/auth/me", headers=auth_headers(evaluator_token)).json()

    resp = client.patch(
        f"/admin/users/{eval_user['id']}",
        headers=auth_headers(sa_token),
        json={"role": "SUPER_ADMIN"},
    )
    assert resp.status_code == 403


# ── Invitations ─────────────────────────────────────────────────────────────

def test_create_invitation(client: TestClient, admin_token: str):
    resp = client.post(
        "/admin/invitations",
        headers=auth_headers(admin_token),
        json={"email": "invite@test.com", "role": "EVALUATOR"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "invite@test.com"
    assert data["role"] == "EVALUATOR"
    assert data["used"] is False


def test_create_invitation_duplicate_email_409(client: TestClient, admin_token: str):
    """Cannot create second invitation for same email if one is pending."""
    client.post("/admin/invitations", headers=auth_headers(admin_token),
                json={"email": "dup@test.com", "role": "EVALUATOR"})
    resp = client.post("/admin/invitations", headers=auth_headers(admin_token),
                       json={"email": "dup@test.com", "role": "EVALUATOR"})
    assert resp.status_code == 409


def test_create_invitation_existing_user_409(client: TestClient, admin_token: str):
    """Cannot invite an email that's already registered."""
    resp = client.post("/admin/invitations", headers=auth_headers(admin_token),
                       json={"email": "admin@test.com", "role": "EVALUATOR"})
    assert resp.status_code == 409


def test_create_invitation_non_admin_403(client: TestClient, evaluator_token: str):
    resp = client.post("/admin/invitations", headers=auth_headers(evaluator_token),
                       json={"email": "inv@test.com", "role": "EVALUATOR"})
    assert resp.status_code == 403


def test_list_invitations(client: TestClient, admin_token: str):
    client.post("/admin/invitations", headers=auth_headers(admin_token),
                json={"email": "list1@test.com", "role": "EVALUATOR"})
    resp = client.get("/admin/invitations", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_revoke_invitation(client: TestClient, admin_token: str):
    inv_id = client.post("/admin/invitations", headers=auth_headers(admin_token),
                         json={"email": "revoke@test.com", "role": "EVALUATOR"}).json()["id"]
    resp = client.delete(f"/admin/invitations/{inv_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Revoked invitation should no longer show in list (it's marked used)
    invitations = client.get("/admin/invitations", headers=auth_headers(admin_token)).json()
    revoked = [i for i in invitations if i["email"] == "revoke@test.com" and not i["used"]]
    assert len(revoked) == 0


def test_resend_invitation(client: TestClient, admin_token: str):
    inv = client.post("/admin/invitations", headers=auth_headers(admin_token),
                      json={"email": "resend@test.com", "role": "EVALUATOR"}).json()
    resp = client.post(f"/admin/invitations/{inv['id']}/resend", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "resend@test.com"


def test_revoke_then_resend_fails(client: TestClient, admin_token: str):
    """Cannot resend a revoked invitation."""
    inv_id = client.post("/admin/invitations", headers=auth_headers(admin_token),
                         json={"email": "rr@test.com", "role": "EVALUATOR"}).json()["id"]
    client.delete(f"/admin/invitations/{inv_id}", headers=auth_headers(admin_token))
    resp = client.post(f"/admin/invitations/{inv_id}/resend", headers=auth_headers(admin_token))
    assert resp.status_code == 400


def test_invitation_not_found_404(client: TestClient, admin_token: str):
    resp = client.delete("/admin/invitations/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404
