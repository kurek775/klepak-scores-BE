"""Tests for /participants endpoints — CRUD, move between groups."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


CSV = b"display_name,group_name\nAlice,Group1\nBob,Group2\n"


def _import_event(client: TestClient, token: str):
    resp = client.post(
        "/events/import",
        headers=auth_headers(token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Participant Test"},
    )
    event_id = resp.json()["event_id"]
    event = client.get(f"/events/{event_id}", headers=auth_headers(token)).json()
    return event_id, event


# ── Add participant ─────────────────────────────────────────────────────────

def test_add_participant(client: TestClient, admin_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]

    resp = client.post(
        f"/groups/{group['id']}/participants",
        headers=auth_headers(admin_token),
        json={"display_name": "Charlie", "gender": "M", "age": 25},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["display_name"] == "Charlie"
    assert data["gender"] == "M"
    assert data["age"] == 25


def test_add_participant_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]

    resp = client.post(
        f"/groups/{group['id']}/participants",
        headers=auth_headers(evaluator_token),
        json={"display_name": "X"},
    )
    assert resp.status_code == 403


def test_add_participant_group_not_found_404(client: TestClient, admin_token: str):
    resp = client.post(
        "/groups/9999/participants",
        headers=auth_headers(admin_token),
        json={"display_name": "Ghost"},
    )
    assert resp.status_code == 404


# ── Update participant ──────────────────────────────────────────────────────

def test_update_participant(client: TestClient, admin_token: str):
    event_id, event = _import_event(client, admin_token)
    participant = event["groups"][0]["participants"][0]

    resp = client.patch(
        f"/participants/{participant['id']}",
        headers=auth_headers(admin_token),
        json={"display_name": "Alice Updated", "age": 30},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Alice Updated"
    assert resp.json()["age"] == 30


def test_update_participant_not_found_404(client: TestClient, admin_token: str):
    resp = client.patch(
        "/participants/9999",
        headers=auth_headers(admin_token),
        json={"display_name": "Nobody"},
    )
    assert resp.status_code == 404


def test_update_participant_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    participant = event["groups"][0]["participants"][0]

    resp = client.patch(
        f"/participants/{participant['id']}",
        headers=auth_headers(evaluator_token),
        json={"display_name": "Nope"},
    )
    assert resp.status_code == 403


# ── Delete participant ──────────────────────────────────────────────────────

def test_delete_participant(client: TestClient, admin_token: str):
    event_id, event = _import_event(client, admin_token)
    participant = event["groups"][0]["participants"][0]

    resp = client.delete(f"/participants/{participant['id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Verify participant is gone by checking event detail
    event_after = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group1_participants = next(g for g in event_after["groups"] if g["name"] == "Group1")["participants"]
    assert not any(p["id"] == participant["id"] for p in group1_participants)


def test_delete_participant_not_found_404(client: TestClient, admin_token: str):
    resp = client.delete("/participants/9999", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── Move participant ────────────────────────────────────────────────────────

def test_move_participant_between_groups(client: TestClient, admin_token: str):
    event_id, event = _import_event(client, admin_token)
    group1 = next(g for g in event["groups"] if g["name"] == "Group1")
    group2 = next(g for g in event["groups"] if g["name"] == "Group2")
    alice = group1["participants"][0]

    resp = client.post(
        f"/participants/{alice['id']}/move",
        headers=auth_headers(admin_token),
        json={"group_id": group2["id"]},
    )
    assert resp.status_code == 200

    # Verify Alice moved to Group2
    event_after = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group2_after = next(g for g in event_after["groups"] if g["name"] == "Group2")
    assert any(p["id"] == alice["id"] for p in group2_after["participants"])


def test_move_participant_cross_event_fails(client: TestClient, admin_token: str):
    """Cannot move participant to a group in a different event."""
    _, event1 = _import_event(client, admin_token)
    _, event2 = _import_event(client, admin_token)

    alice = event1["groups"][0]["participants"][0]
    other_group = event2["groups"][0]

    resp = client.post(
        f"/participants/{alice['id']}/move",
        headers=auth_headers(admin_token),
        json={"group_id": other_group["id"]},
    )
    assert resp.status_code == 400


def test_move_participant_not_found_404(client: TestClient, admin_token: str):
    _, event = _import_event(client, admin_token)
    group = event["groups"][0]

    resp = client.post(
        "/participants/9999/move",
        headers=auth_headers(admin_token),
        json={"group_id": group["id"]},
    )
    assert resp.status_code == 404


def test_move_participant_target_group_not_found_404(client: TestClient, admin_token: str):
    _, event = _import_event(client, admin_token)
    alice = event["groups"][0]["participants"][0]

    resp = client.post(
        f"/participants/{alice['id']}/move",
        headers=auth_headers(admin_token),
        json={"group_id": 9999},
    )
    assert resp.status_code == 404
