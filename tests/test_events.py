"""Tests for /events endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers

VALID_CSV = b"display_name,group_name\nAlice,TeamA\nBob,TeamA\nCarol,TeamB\n"
BAD_CSV = b"name,team\nAlice,TeamA\n"  # missing required columns


def _import_event(client: TestClient, token: str, csv_bytes: bytes = VALID_CSV, event_name: str = "Test Event"):
    return client.post(
        "/events/import",
        headers=auth_headers(token),
        files={"file": ("participants.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"event_name": event_name},
    )


# ── Import ──────────────────────────────────────────────────────────────────

def test_import_event_success(client: TestClient, admin_token: str):
    resp = _import_event(client, admin_token)
    assert resp.status_code == 201
    data = resp.json()
    assert data["groups_created"] == 2
    assert data["participants_created"] == 3
    assert data["event_name"] == "Test Event"


def test_import_event_bad_csv_400(client: TestClient, admin_token: str):
    resp = _import_event(client, admin_token, csv_bytes=BAD_CSV)
    assert resp.status_code == 400


def test_import_event_non_admin_403(client: TestClient, evaluator_token: str):
    resp = _import_event(client, evaluator_token)
    assert resp.status_code == 403


# ── List / Get ───────────────────────────────────────────────────────────────

def test_list_events(client: TestClient, admin_token: str):
    _import_event(client, admin_token)
    resp = client.get("/events", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_event_detail(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token).json()["event_id"]
    resp = client.get(f"/events/{event_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["groups"]) == 2


def test_get_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.get("/events/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── Delete ───────────────────────────────────────────────────────────────────

def test_delete_event(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token).json()["event_id"]
    resp = client.delete(f"/events/{event_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204
    # Should be 404 after deletion
    resp2 = client.get(f"/events/{event_id}", headers=auth_headers(admin_token))
    assert resp2.status_code == 404


def test_delete_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.delete("/events/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── Age categories ───────────────────────────────────────────────────────────

def test_age_category_crud(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token).json()["event_id"]
    base_url = f"/events/{event_id}/age-categories"

    # Create
    resp = client.post(
        base_url,
        headers=auth_headers(admin_token),
        json={"name": "Junior", "min_age": 0, "max_age": 17},
    )
    assert resp.status_code == 201
    cat_id = resp.json()["id"]

    # List
    resp = client.get(base_url, headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Delete
    resp = client.delete(f"{base_url}/{cat_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # List again — should be empty
    resp = client.get(base_url, headers=auth_headers(admin_token))
    assert resp.json() == []


def test_delete_age_category_wrong_event_404(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token).json()["event_id"]
    cat_id = client.post(
        f"/events/{event_id}/age-categories",
        headers=auth_headers(admin_token),
        json={"name": "Senior", "min_age": 18, "max_age": 99},
    ).json()["id"]

    # Try deleting with a different event_id
    resp = client.delete(f"/events/9999/age-categories/{cat_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 404
