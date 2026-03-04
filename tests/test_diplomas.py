"""Tests for /events/{event_id}/diplomas endpoints — template CRUD."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


CSV = b"display_name,group_name\nAlice,Group1\n"

DIPLOMA_BODY = {
    "name": "Test Template",
    "orientation": "LANDSCAPE",
    "items": [],
    "fonts": [],
    "default_font": None,
}


def _import_event(client: TestClient, token: str) -> int:
    resp = client.post(
        "/events/import",
        headers=auth_headers(token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Diploma Test"},
    )
    return resp.json()["event_id"]


# ── List diploma templates ──────────────────────────────────────────────────

def test_list_diploma_templates(client: TestClient, admin_token: str):
    """Import creates a default diploma template."""
    event_id = _import_event(client, admin_token)
    resp = client.get(f"/events/{event_id}/diplomas", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    # Import auto-creates a default template
    assert len(resp.json()) >= 1


def test_list_diplomas_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.get("/events/9999/diplomas", headers=auth_headers(admin_token))
    assert resp.status_code == 404


def test_list_diplomas_evaluator_can_read(client: TestClient, admin_token: str, evaluator_token: str):
    """Any authenticated user can read diploma templates."""
    event_id = _import_event(client, admin_token)
    resp = client.get(f"/events/{event_id}/diplomas", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200


# ── Create diploma template ─────────────────────────────────────────────────

def test_create_diploma_template(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.post(
        f"/events/{event_id}/diplomas",
        headers=auth_headers(admin_token),
        json=DIPLOMA_BODY,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Template"
    assert data["orientation"] == "LANDSCAPE"
    assert data["event_id"] == event_id


def test_create_diploma_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.post(
        f"/events/{event_id}/diplomas",
        headers=auth_headers(evaluator_token),
        json=DIPLOMA_BODY,
    )
    assert resp.status_code == 403


def test_create_diploma_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.post("/events/9999/diplomas", headers=auth_headers(admin_token), json=DIPLOMA_BODY)
    assert resp.status_code == 404


# ── Get single diploma template ─────────────────────────────────────────────

def test_get_diploma_template(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    template_id = client.post(
        f"/events/{event_id}/diplomas", headers=auth_headers(admin_token), json=DIPLOMA_BODY,
    ).json()["id"]

    resp = client.get(f"/events/{event_id}/diplomas/{template_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Template"


def test_get_diploma_template_not_found_404(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.get(f"/events/{event_id}/diplomas/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── Update diploma template ─────────────────────────────────────────────────

def test_update_diploma_template(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    template_id = client.post(
        f"/events/{event_id}/diplomas", headers=auth_headers(admin_token), json=DIPLOMA_BODY,
    ).json()["id"]

    resp = client.put(
        f"/events/{event_id}/diplomas/{template_id}",
        headers=auth_headers(admin_token),
        json={"name": "Updated Template", "orientation": "PORTRAIT"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Template"
    assert resp.json()["orientation"] == "PORTRAIT"


def test_update_diploma_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    template_id = client.post(
        f"/events/{event_id}/diplomas", headers=auth_headers(admin_token), json=DIPLOMA_BODY,
    ).json()["id"]

    resp = client.put(
        f"/events/{event_id}/diplomas/{template_id}",
        headers=auth_headers(evaluator_token),
        json={"name": "Nope"},
    )
    assert resp.status_code == 403


# ── Delete diploma template ─────────────────────────────────────────────────

def test_delete_diploma_template(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    template_id = client.post(
        f"/events/{event_id}/diplomas", headers=auth_headers(admin_token), json=DIPLOMA_BODY,
    ).json()["id"]

    resp = client.delete(f"/events/{event_id}/diplomas/{template_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Verify template is gone
    resp2 = client.get(f"/events/{event_id}/diplomas/{template_id}", headers=auth_headers(admin_token))
    assert resp2.status_code == 404


def test_delete_diploma_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    template_id = client.post(
        f"/events/{event_id}/diplomas", headers=auth_headers(admin_token), json=DIPLOMA_BODY,
    ).json()["id"]

    resp = client.delete(
        f"/events/{event_id}/diplomas/{template_id}",
        headers=auth_headers(evaluator_token),
    )
    assert resp.status_code == 403


def test_delete_diploma_not_found_404(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.delete(f"/events/{event_id}/diplomas/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404
