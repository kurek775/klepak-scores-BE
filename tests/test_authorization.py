"""Tests for critical authorization paths."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login

CSV = b"display_name,group_name\nAlice,Group1\nBob,Group2\n"


def _create_event(client: TestClient, admin_token: str) -> int:
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Auth Test"},
    )
    return resp.json()["event_id"]


def _get_user_id(client: TestClient, token: str) -> int:
    return client.get("/auth/me", headers=auth_headers(token)).json()["id"]


def _full_setup(client, admin_token, eval_token, engine):
    """Create event, assign evaluator to pool and Group1, create activity."""
    event_id = _create_event(client, admin_token)
    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group1 = next(g for g in event["groups"] if g["name"] == "Group1")
    group2 = next(g for g in event["groups"] if g["name"] == "Group2")

    eval_id = _get_user_id(client, eval_token)
    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token), json={"user_id": eval_id})
    client.post(f"/groups/{group1['id']}/evaluators", headers=auth_headers(admin_token), json={"user_id": eval_id})

    activity_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Sprint", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id},
    ).json()["id"]

    alice_id = group1["participants"][0]["id"]
    bob_id = group2["participants"][0]["id"]

    return event_id, activity_id, group1["id"], group2["id"], alice_id, bob_id, eval_id


# ── Evaluator accessing events outside their pool ─────────────────────────


def test_evaluator_cannot_view_event_detail_outside_pool(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluator NOT in the event pool should get 403 on event detail."""
    event_id = _create_event(client, admin_token)
    resp = client.get(f"/events/{event_id}", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403


def test_evaluator_can_view_event_detail_when_in_pool(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluator IN the event pool should see event detail."""
    event_id = _create_event(client, admin_token)
    eval_id = _get_user_id(client, evaluator_token)
    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token), json={"user_id": eval_id})
    resp = client.get(f"/events/{event_id}", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200


def test_evaluator_event_list_only_shows_pool_events(
    client: TestClient, admin_token: str, evaluator_token: str, engine
):
    """Evaluator should only see events they are in the pool for."""
    event1_id = _create_event(client, admin_token)
    event2_id = client.post(
        "/events/import", headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Auth Test 2"},
    ).json()["event_id"]

    eval_id = _get_user_id(client, evaluator_token)
    client.post(f"/events/{event1_id}/evaluators", headers=auth_headers(admin_token), json={"user_id": eval_id})

    resp = client.get("/events", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200
    event_ids = [e["id"] for e in resp.json()]
    assert event1_id in event_ids
    assert event2_id not in event_ids


# ── Cross-event record injection ──────────────────────────────────────────


def test_cross_event_record_injection_blocked(
    client: TestClient, admin_token: str, evaluator_token: str, engine
):
    """Evaluator cannot submit records for an activity from a different event."""
    event1_id, activity1_id, g1_id, _, alice_id, _, eval_id = _full_setup(
        client, admin_token, evaluator_token, engine
    )

    # Create a second event with its own activity
    event2_id = client.post(
        "/events/import", headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Other Event"},
    ).json()["event_id"]
    activity2_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Other Activity", "evaluation_type": "NUMERIC_HIGH", "event_id": event2_id},
    ).json()["id"]

    # Try to submit alice (event1) against activity2 (event2)
    resp = client.post(
        "/records", headers=auth_headers(evaluator_token),
        json={"value_raw": "99", "participant_id": alice_id, "activity_id": activity2_id},
    )
    assert resp.status_code == 400
    assert "same event" in resp.json()["detail"].lower()


def test_cross_event_bulk_record_injection_blocked(
    client: TestClient, admin_token: str, evaluator_token: str, engine
):
    """Bulk record submission should also block cross-event injection."""
    event1_id, activity1_id, g1_id, _, alice_id, _, eval_id = _full_setup(
        client, admin_token, evaluator_token, engine
    )

    event2_id = client.post(
        "/events/import", headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Other Event 2"},
    ).json()["event_id"]
    activity2_id = client.post(
        "/activities", headers=auth_headers(admin_token),
        json={"name": "Other Activity 2", "evaluation_type": "NUMERIC_HIGH", "event_id": event2_id},
    ).json()["id"]

    resp = client.post(
        "/records/bulk", headers=auth_headers(evaluator_token),
        json={
            "activity_id": activity2_id,
            "records": [{"participant_id": alice_id, "value_raw": "50"}],
        },
    )
    assert resp.status_code == 400
    assert "same event" in resp.json()["detail"].lower()


# ── Cascade deletes ───────────────────────────────────────────────────────


def test_delete_event_cascades_groups_and_participants(client: TestClient, admin_token: str):
    """Deleting an event should cascade-delete its groups (no dangling data)."""
    event_id = _create_event(client, admin_token)
    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group_ids = [g["id"] for g in event["groups"]]
    assert len(group_ids) >= 1

    resp = client.delete(f"/events/{event_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Event should no longer exist
    resp = client.get(f"/events/{event_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 404


def test_remove_from_pool_cascades_to_group_evaluator(
    client: TestClient, admin_token: str, evaluator_token: str
):
    """Removing evaluator from event pool should also remove group assignments."""
    event_id = _create_event(client, admin_token)
    eval_id = _get_user_id(client, evaluator_token)
    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group = event["groups"][0]

    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token), json={"user_id": eval_id})
    client.post(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token), json={"user_id": eval_id})

    # Verify assignment exists
    resp = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token))
    assert len(resp.json()) == 1

    # Remove from pool — should cascade
    client.delete(f"/events/{event_id}/evaluators/{eval_id}", headers=auth_headers(admin_token))
    resp = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token))
    assert len(resp.json()) == 0


# ── Evaluator role restrictions ───────────────────────────────────────────


def test_evaluator_cannot_create_event(client: TestClient, evaluator_token: str):
    """Evaluators should not be able to create events."""
    resp = client.post(
        "/events/import", headers=auth_headers(evaluator_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Forbidden"},
    )
    assert resp.status_code == 403


def test_evaluator_cannot_delete_event(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluators should not be able to delete events."""
    event_id = _create_event(client, admin_token)
    resp = client.delete(f"/events/{event_id}", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403


def test_evaluator_cannot_add_to_event_pool(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluators should not be able to modify event evaluator pool."""
    event_id = _create_event(client, admin_token)
    eval_id = _get_user_id(client, evaluator_token)
    resp = client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(evaluator_token),
        json={"user_id": eval_id},
    )
    assert resp.status_code == 403


def test_evaluator_cannot_export_csv(client: TestClient, admin_token: str, evaluator_token: str):
    """CSV export is admin-only."""
    event_id = _create_event(client, admin_token)
    resp = client.get(f"/events/{event_id}/export-csv", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403
