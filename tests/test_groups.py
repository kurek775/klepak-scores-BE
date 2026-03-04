"""Tests for /groups endpoints — CRUD, evaluator assignment."""

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
        data={"event_name": "Group Test Event"},
    )
    event_id = resp.json()["event_id"]
    event = client.get(f"/events/{event_id}", headers=auth_headers(token)).json()
    return event_id, event


def _get_eval_id(client: TestClient, eval_token: str) -> int:
    return client.get("/auth/me", headers=auth_headers(eval_token)).json()["id"]


# ── My groups ───────────────────────────────────────────────────────────────

def test_my_groups_empty(client: TestClient, evaluator_token: str):
    """Evaluator with no assignments gets empty list."""
    resp = client.get("/groups/my-groups", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_my_groups_after_assignment(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group1 = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    # Add to event pool, then assign to group
    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})
    client.post(f"/groups/{group1['id']}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    resp = client.get("/groups/my-groups", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200
    groups = resp.json()
    assert len(groups) == 1
    assert groups[0]["event_name"] == "Group Test Event"


# ── Update group ────────────────────────────────────────────────────────────

def test_update_group_name(client: TestClient, admin_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]

    resp = client.patch(
        f"/groups/{group['id']}",
        headers=auth_headers(admin_token),
        json={"name": "Renamed Group"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Group"


def test_update_group_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]

    resp = client.patch(
        f"/groups/{group['id']}",
        headers=auth_headers(evaluator_token),
        json={"name": "Nope"},
    )
    assert resp.status_code == 403


def test_update_group_not_found_404(client: TestClient, admin_token: str):
    resp = client.patch("/groups/9999", headers=auth_headers(admin_token), json={"name": "X"})
    assert resp.status_code == 404


# ── Delete group ────────────────────────────────────────────────────────────

def test_delete_group_with_participants_fails(client: TestClient, admin_token: str):
    """Cannot delete group that still has participants."""
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]

    resp = client.delete(f"/groups/{group['id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 400


def test_delete_empty_group(client: TestClient, admin_token: str):
    """Can delete a group after removing all participants."""
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]

    # Delete participant from group first
    for p in group["participants"]:
        client.delete(f"/participants/{p['id']}", headers=auth_headers(admin_token))

    resp = client.delete(f"/groups/{group['id']}", headers=auth_headers(admin_token))
    assert resp.status_code == 204


# ── Assign evaluator to group ──────────────────────────────────────────────

def test_assign_evaluator_to_group(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    # Add to event pool first
    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    resp = client.post(
        f"/groups/{group['id']}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    assert resp.status_code == 201


def test_assign_evaluator_not_in_pool_400(client: TestClient, admin_token: str, evaluator_token: str):
    """Must be in event pool first."""
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    resp = client.post(
        f"/groups/{group['id']}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )
    assert resp.status_code == 400


def test_assign_evaluator_duplicate_409(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})
    client.post(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    # Second assignment to same group
    resp = client.post(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token),
                       json={"user_id": eval_id})
    assert resp.status_code == 409


def test_assign_evaluator_to_second_group_same_event_409(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluator can only be in one group per event."""
    event_id, event = _import_event(client, admin_token)
    group1, group2 = event["groups"][0], event["groups"][1]
    eval_id = _get_eval_id(client, evaluator_token)

    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})
    client.post(f"/groups/{group1['id']}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    resp = client.post(f"/groups/{group2['id']}/evaluators", headers=auth_headers(admin_token),
                       json={"user_id": eval_id})
    assert resp.status_code == 409


# ── Remove evaluator from group ────────────────────────────────────────────

def test_remove_evaluator_from_group(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})
    client.post(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    resp = client.delete(f"/groups/{group['id']}/evaluators/{eval_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # Verify evaluator no longer in group
    evals = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token)).json()
    assert len(evals) == 0


def test_remove_evaluator_not_assigned_404(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    resp = client.delete(f"/groups/{group['id']}/evaluators/{eval_id}", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── List group evaluators ──────────────────────────────────────────────────

def test_list_group_evaluators_admin(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})
    client.post(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    resp = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_group_evaluators_evaluator_own_group(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluator can see evaluators of their own group."""
    event_id, event = _import_event(client, admin_token)
    group = event["groups"][0]
    eval_id = _get_eval_id(client, evaluator_token)

    client.post(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})
    client.post(f"/groups/{group['id']}/evaluators", headers=auth_headers(admin_token),
                json={"user_id": eval_id})

    resp = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(evaluator_token))
    assert resp.status_code == 200


def test_list_group_evaluators_evaluator_other_group_403(client: TestClient, admin_token: str, evaluator_token: str):
    """Evaluator cannot see evaluators of a group they're not in."""
    event_id, event = _import_event(client, admin_token)
    # Evaluator is not assigned to any group
    group = event["groups"][1]

    resp = client.get(f"/groups/{group['id']}/evaluators", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403
