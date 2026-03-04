"""Tests for /admin/audit-logs endpoint — pagination, admin-only access."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


# ── Audit logs ──────────────────────────────────────────────────────────────

def test_audit_logs_after_register(client: TestClient, admin_token: str):
    """Registration creates an audit log entry."""
    resp = client.get("/admin/audit-logs", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1
    # Should contain at least the REGISTER and LOGIN actions from fixture setup
    actions = [item["action"] for item in data["items"]]
    assert "REGISTER" in actions or "LOGIN" in actions


def test_audit_logs_pagination(client: TestClient, admin_token: str):
    resp = client.get("/admin/audit-logs?skip=0&limit=1", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 1
    assert data["skip"] == 0
    assert data["limit"] == 1


def test_audit_logs_skip(client: TestClient, admin_token: str):
    """Skip returns offset results."""
    resp_all = client.get("/admin/audit-logs?limit=100", headers=auth_headers(admin_token))
    total = resp_all.json()["total"]

    resp_skip = client.get(f"/admin/audit-logs?skip={total}", headers=auth_headers(admin_token))
    assert resp_skip.json()["items"] == []


def test_audit_logs_non_admin_403(client: TestClient, evaluator_token: str):
    resp = client.get("/admin/audit-logs", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403


def test_audit_logs_unauthenticated_401(client: TestClient):
    resp = client.get("/admin/audit-logs")
    assert resp.status_code == 401
