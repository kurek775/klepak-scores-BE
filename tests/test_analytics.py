"""Tests for leaderboard and CSV export endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers

# All participants in a single group so one evaluator covers everyone
VALID_CSV = b"display_name,group_name,age,gender\nAlice,Team1,20,F\nBob,Team1,25,M\nCarol,Team1,22,F\n"


def _setup(client: TestClient, admin_token: str, eval_token: str, eval_type: str = "NUMERIC_LOW"):
    """Import event, create activity, assign evaluator, return (event_id, activity_id, participants)."""
    event_id = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(VALID_CSV), "text/csv")},
        data={"event_name": "LB Test"},
    ).json()["event_id"]

    event = client.get(f"/events/{event_id}", headers=auth_headers(admin_token)).json()
    group = event["groups"][0]

    eval_id = client.get("/auth/me", headers=auth_headers(eval_token)).json()["id"]
    client.post(
        f"/groups/{group['id']}/evaluators",
        headers=auth_headers(admin_token),
        json={"user_id": eval_id},
    )

    activity_id = client.post(
        "/activities",
        headers=auth_headers(admin_token),
        json={"name": "Sprint", "evaluation_type": eval_type, "event_id": event_id},
    ).json()["id"]

    participants = {p["display_name"]: p["id"] for p in group["participants"]}
    return event_id, activity_id, participants


def test_leaderboard_returns_200(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, activity_id, participants = _setup(client, admin_token, evaluator_token)
    client.post("/records/bulk", headers=auth_headers(evaluator_token), json={
        "activity_id": activity_id,
        "records": [
            {"participant_id": participants["Alice"], "value_raw": "10"},
            {"participant_id": participants["Bob"], "value_raw": "20"},
        ],
    })
    resp = client.get(f"/events/{event_id}/leaderboard", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event_id
    assert len(data["activities"]) == 1


def test_leaderboard_numeric_low_sorting(client: TestClient, admin_token: str, evaluator_token: str):
    """NUMERIC_LOW: lower score = higher rank (rank 1 is smallest value)."""
    event_id, activity_id, participants = _setup(client, admin_token, evaluator_token, "NUMERIC_LOW")
    client.post("/records/bulk", headers=auth_headers(evaluator_token), json={
        "activity_id": activity_id,
        "records": [
            {"participant_id": participants["Alice"], "value_raw": "10"},
            {"participant_id": participants["Carol"], "value_raw": "15"},
        ],
    })
    data = client.get(f"/events/{event_id}/leaderboard", headers=auth_headers(admin_token)).json()
    female_cat = next(c for c in data["activities"][0]["categories"] if c["gender"] == "F")
    alice = next(p for p in female_cat["participants"] if p["display_name"] == "Alice")
    carol = next(p for p in female_cat["participants"] if p["display_name"] == "Carol")
    assert alice["rank"] < carol["rank"]


def test_leaderboard_tie_same_rank(client: TestClient, admin_token: str, evaluator_token: str):
    """Two participants with identical scores share the same rank."""
    event_id, activity_id, participants = _setup(client, admin_token, evaluator_token, "NUMERIC_HIGH")
    client.post("/records/bulk", headers=auth_headers(evaluator_token), json={
        "activity_id": activity_id,
        "records": [
            {"participant_id": participants["Alice"], "value_raw": "100"},
            {"participant_id": participants["Carol"], "value_raw": "100"},
        ],
    })
    data = client.get(f"/events/{event_id}/leaderboard", headers=auth_headers(admin_token)).json()
    female_cat = next(c for c in data["activities"][0]["categories"] if c["gender"] == "F")
    ranks = [p["rank"] for p in female_cat["participants"]]
    assert len(set(ranks)) == 1  # all same rank


def test_leaderboard_not_found_404(client: TestClient, admin_token: str):
    resp = client.get("/events/9999/leaderboard", headers=auth_headers(admin_token))
    assert resp.status_code == 404


def test_export_csv_admin_200(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, activity_id, participants = _setup(client, admin_token, evaluator_token)
    client.post("/records/bulk", headers=auth_headers(evaluator_token), json={
        "activity_id": activity_id,
        "records": [{"participant_id": participants["Alice"], "value_raw": "10"}],
    })
    resp = client.get(f"/events/{event_id}/export-csv", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Alice" in resp.text


def test_export_csv_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id, _, _ = _setup(client, admin_token, evaluator_token)
    resp = client.get(f"/events/{event_id}/export-csv", headers=auth_headers(evaluator_token))
    assert resp.status_code == 403
