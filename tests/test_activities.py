"""Tests for /activities endpoints — CRUD."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


CSV = b"display_name,group_name\nAlice,Group1\n"


def _import_event(client: TestClient, token: str) -> int:
    resp = client.post(
        "/events/import",
        headers=auth_headers(token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Activity Test"},
    )
    return resp.json()["event_id"]


# ── Create activity ─────────────────────────────────────────────────────────

def test_create_activity(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.post(
        "/activities",
        headers=auth_headers(admin_token),
        json={"name": "Sprint", "evaluation_type": "NUMERIC_LOW", "event_id": event_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Sprint"
    assert data["evaluation_type"] == "NUMERIC_LOW"
    assert data["event_id"] == event_id


def test_create_activity_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.post(
        "/activities",
        headers=auth_headers(evaluator_token),
        json={"name": "Nope", "evaluation_type": "BOOLEAN", "event_id": event_id},
    )
    assert resp.status_code == 403


def test_create_activity_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.post(
        "/activities",
        headers=auth_headers(admin_token),
        json={"name": "Ghost", "evaluation_type": "BOOLEAN", "event_id": 9999},
    )
    assert resp.status_code == 404


# ── List activities ─────────────────────────────────────────────────────────

def test_list_event_activities(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    client.post("/activities", headers=auth_headers(admin_token),
                json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id})
    client.post("/activities", headers=auth_headers(admin_token),
                json={"name": "Run", "evaluation_type": "NUMERIC_LOW", "event_id": event_id})

    resp = client.get(f"/events/{event_id}/activities", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_activities_evaluator_can_read(client: TestClient, admin_token: str, evaluator_token: str):
    """Any authenticated user can list activities."""
    event_id = _import_event(client, admin_token)
    client.post("/activities", headers=auth_headers(admin_token),
                json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id})

    resp = client.get(f"/events/{event_id}/activities", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_activities_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.get("/events/9999/activities", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── Update activity ─────────────────────────────────────────────────────────

def test_update_activity(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    activity_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id},
    ).json()["id"]

    resp = client.patch(
        f"/activities/{activity_id}",
        headers=auth_headers(admin_token),
        json={"name": "High Jump", "description": "Jumping high"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "High Jump"
    assert resp.json()["description"] == "Jumping high"


def test_update_activity_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    activity_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id},
    ).json()["id"]

    resp = client.patch(
        f"/activities/{activity_id}",
        headers=auth_headers(evaluator_token),
        json={"name": "Nope"},
    )
    assert resp.status_code == 403


def test_update_activity_not_found_404(client: TestClient, admin_token: str):
    resp = client.patch("/activities/9999", headers=auth_headers(admin_token), json={"name": "X"})
    assert resp.status_code == 404


# ── Delete activity ─────────────────────────────────────────────────────────

def test_delete_activity(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    activity_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id},
    ).json()["id"]

    resp = client.delete(f"/activities/{activity_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Verify activity is gone
    activities = client.get(f"/events/{event_id}/activities", headers=auth_headers(admin_token)).json()
    assert len(activities) == 0


def test_delete_activity_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    activity_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id},
    ).json()["id"]

    resp = client.delete(f"/activities/{activity_id}", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403


def test_delete_activity_not_found_404(client: TestClient, admin_token: str):
    resp = client.delete("/activities/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404
