"""Tests for /auth endpoints."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_register_first_user_becomes_admin(client: TestClient):
    resp = client.post(
        "/auth/register",
        json={"email": "first@test.com", "password": "Password1!", "full_name": "First User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True


def test_register_second_user_becomes_evaluator(client: TestClient):
    client.post("/auth/register", json={"email": "a@test.com", "password": "Password1!", "full_name": "A"})
    resp = client.post("/auth/register", json={"email": "b@test.com", "password": "Password1!", "full_name": "B"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "EVALUATOR"
    assert data["is_active"] is False


def test_register_duplicate_email_409(client: TestClient):
    client.post("/auth/register", json={"email": "dup@test.com", "password": "Password1!", "full_name": "Dup"})
    resp = client.post("/auth/register", json={"email": "dup@test.com", "password": "Password1!", "full_name": "Dup2"})
    assert resp.status_code == 409


def test_register_weak_password_422(client: TestClient):
    resp = client.post(
        "/auth/register",
        json={"email": "weak@test.com", "password": "short", "full_name": "Weak"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert any("8 characters" in str(e) for e in body["detail"])


def test_login_success(client: TestClient):
    client.post("/auth/register", json={"email": "user@test.com", "password": "Password1!", "full_name": "User"})
    resp = client.post("/auth/login", json={"email": "user@test.com", "password": "Password1!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_401(client: TestClient):
    client.post("/auth/register", json={"email": "user2@test.com", "password": "Password1!", "full_name": "User"})
    resp = client.post("/auth/login", json={"email": "user2@test.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_nonexistent_user_401(client: TestClient):
    resp = client.post("/auth/login", json={"email": "nobody@test.com", "password": "Password1!"})
    assert resp.status_code == 401


def test_me_returns_current_user(client: TestClient, admin_token: str):
    resp = client.get("/auth/me", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.com"


def test_me_without_token_401(client: TestClient):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
