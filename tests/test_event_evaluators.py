"""Tests for event evaluator pool endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers

CSV = b"display_name,group_name\nAlice,Group1\nBob,Group2\n"


def _create_event(client: TestClient, admin_token: str) -> int:
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Pool Test"},
    )
    return resp.json()["event_id"]


def _get_eval_id(client: TestClient, eval_token: str) -> int:
    return client.get("/auth/me", headers=auth_headers(eval_token)).json()["id"]


def test_add_evaluator_to_event_pool(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)
    resp = client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    assert resp.status_code == 201
    assert resp.json()["detail"] == "Evaluator added to event"


def test_list_event_evaluators(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)
    client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    resp = client.get(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    evals = resp.json()
    assert len(evals) == 1
    assert evals[0]["id"] == eval_id


def test_remove_evaluator_from_event_pool(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)
    client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    resp = client.delete(
        f"/events/{event_id}/evaluators/{eval_id}",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 204

    # Verify empty pool
    resp = client.get(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token))
    assert len(resp.json()) == 0


def test_duplicate_pool_assignment_409(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)
    client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    resp = client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    assert resp.status_code == 409


def test_group_assignment_requires_event_pool(client: TestClient, admin_token: str, evaluator_token: str):
    """Assigning evaluator to a group without event pool membership should fail."""
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)

    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group = event["groups"][0]

    resp = client.post(
        f"/groups/{group['id']}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    assert resp.status_code == 400
    assert "event" in resp.json()["detail"].lower()


def test_remove_from_pool_cascades_group_assignment(client: TestClient, admin_token: str, evaluator_token: str):
    """Removing from event pool should also remove group assignments."""
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)

    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group = event["groups"][0]

    # Add to pool, then assign to group
    client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    client.post(
        f"/groups/{group['id']}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )

    # Remove from pool
    client.delete(
        f"/events/{event_id}/evaluators/{eval_id}",
        headers=auth_headers(admin_token),
    )

    # Group assignment should also be gone
    resp = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token))
    assert len(resp.json()) == 0


def test_event_detail_includes_pool(client: TestClient, admin_token: str, evaluator_token: str):
    """GET /events/{id} should include event_evaluators."""
    event_id = _create_event(client, admin_token)
    eval_id = _get_eval_id(client, evaluator_token)
    client.post(
        f"/events/{event_id}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    resp = client.get(f"/events/{event_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "event_evaluators" in data
    assert len(data["event_evaluators"]) == 1
    assert data["event_evaluators"][0]["id"] == eval_id
