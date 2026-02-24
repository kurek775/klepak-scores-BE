"""Tests for /records endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers

CSV = b"display_name,group_name\nAlice,Group1\nBob,Group2\n"


def _setup(client: TestClient, admin_token: str, eval_token: str):
    """
    Import 2-group event. Assign evaluator to Group1 only.
    Returns (event_id, activity_id, alice_id, bob_id, eval_id).
    """
    event_id = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Records Test"},
    ).json()["event_id"]

    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group1 = next(g for g in event["groups"] if g["name"] == "Group1")
    group2 = next(g for g in event["groups"] if g["name"] == "Group2")

    eval_id = client.get("/auth/me", headers=auth_headers(eval_token)).json()["id"]
    # Add evaluator to event pool first (Phase 8 requirement)
    client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    client.post(
        f"/groups/{group1['id']}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )

    activity_id = client.post(
        "/activities",
        headers=auth_headers(admin_token),
        json={"name": "Jump", "evaluation_type": "NUMERIC_HIGH", "event_id": event_id},
    ).json()["id"]

    alice_id = group1["participants"][0]["id"]
    bob_id = group2["participants"][0]["id"]

    return event_id, activity_id, alice_id, bob_id, eval_id


def test_submit_single_record(client: TestClient, admin_token: str, evaluator_token: str):
    _, activity_id, alice_id, _, _ = _setup(client, admin_token, evaluator_token)
    resp = client.post(
        "/records",
        headers=auth_headers(evaluator_token),
        json={"value_raw": "42", "participant_id": alice_id, "activity_id": activity_id},
    )
    assert resp.status_code == 201
    assert resp.json()["value_raw"] == "42"


def test_submit_record_upsert(client: TestClient, admin_token: str, evaluator_token: str):
    """Submitting twice for same participant/activity updates the record."""
    _, activity_id, alice_id, _, _ = _setup(client, admin_token, evaluator_token)
    client.post("/records", headers=auth_headers(evaluator_token),
                json={"value_raw": "10", "participant_id": alice_id, "activity_id": activity_id})
    resp = client.post("/records", headers=auth_headers(evaluator_token),
                       json={"value_raw": "99", "participant_id": alice_id, "activity_id": activity_id})
    assert resp.status_code == 201
    assert resp.json()["value_raw"] == "99"


def test_evaluator_cannot_submit_for_unassigned_group(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluator assigned to Group1 cannot submit for Bob who is in Group2."""
    _, activity_id, _, bob_id, _ = _setup(client, admin_token, evaluator_token)
    resp = client.post(
        "/records",
        headers=auth_headers(evaluator_token),
        json={"value_raw": "50", "participant_id": bob_id, "activity_id": activity_id},
    )
    assert resp.status_code == 403


def test_submit_bulk_records(client: TestClient, admin_token: str, evaluator_token: str):
    _, activity_id, alice_id, _, _ = _setup(client, admin_token, evaluator_token)
    resp = client.post(
        "/records/bulk",
        headers=auth_headers(evaluator_token),
        json={
            "activity_id": activity_id,
            "records": [{"participant_id": alice_id, "value_raw": "77"}],
        },
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 1


def test_get_activity_records(client: TestClient, admin_token: str, evaluator_token: str):
    _, activity_id, alice_id, _, _ = _setup(client, admin_token, evaluator_token)
    client.post("/records", headers=auth_headers(evaluator_token),
                json={"value_raw": "5", "participant_id": alice_id, "activity_id": activity_id})
    resp = client.get(f"/activities/{activity_id}/records", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_submit_record_invalid_activity_404(client: TestClient, admin_token: str, evaluator_token: str):
    _, _, alice_id, _, _ = _setup(client, admin_token, evaluator_token)
    resp = client.post(
        "/records",
        headers=auth_headers(evaluator_token),
        json={"value_raw": "1", "participant_id": alice_id, "activity_id": 9999},
    )
    assert resp.status_code == 404
