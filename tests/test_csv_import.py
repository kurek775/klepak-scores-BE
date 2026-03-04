"""Tests for CSV preview and import with column mapping."""

import io
import json

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


STANDARD_CSV = b"display_name,group_name\nAlice,TeamA\nBob,TeamB\n"
CUSTOM_COLUMNS_CSV = b"name,team,id\nAlice,TeamA,001\nBob,TeamB,002\n"
CSV_WITH_METADATA = b"display_name,group_name,shirt_size,shoe_size\nAlice,TeamA,M,42\nBob,TeamB,L,44\n"
EMPTY_CSV = b"display_name,group_name\n"
MISSING_COLUMNS_CSV = b"name,team\nAlice,TeamA\n"


# ── Preview CSV ─────────────────────────────────────────────────────────────

def test_preview_csv(client: TestClient, admin_token: str):
    resp = client.post(
        "/events/preview-csv",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(STANDARD_CSV), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "headers" in data
    assert "sample_rows" in data
    assert "total_rows" in data
    assert data["total_rows"] == 2
    assert "display_name" in data["headers"]
    assert "group_name" in data["headers"]


def test_preview_csv_custom_columns(client: TestClient, admin_token: str):
    resp = client.post(
        "/events/preview-csv",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(CUSTOM_COLUMNS_CSV), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data["headers"]
    assert "team" in data["headers"]


def test_preview_csv_non_admin_403(client: TestClient, evaluator_token: str):
    resp = client.post(
        "/events/preview-csv",
        headers=auth_headers(evaluator_token),
        files={"file": ("data.csv", io.BytesIO(STANDARD_CSV), "text/csv")},
    )
    assert resp.status_code == 403


# ── Import with standard columns ───────────────────────────────────────────

def test_import_standard_csv(client: TestClient, admin_token: str):
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(STANDARD_CSV), "text/csv")},
        data={"event_name": "Standard Import"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["groups_created"] == 2
    assert data["participants_created"] == 2


# ── Import with column mapping ─────────────────────────────────────────────

def test_import_with_column_mapping(client: TestClient, admin_token: str):
    """Map custom CSV columns to expected fields."""
    # Keys are CSV column names, values are system field names
    mapping = json.dumps({"name": "display_name", "team": "group_name", "id": "external_id"})
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(CUSTOM_COLUMNS_CSV), "text/csv")},
        data={"event_name": "Mapped Import", "column_mapping": mapping},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["participants_created"] == 2

    # Verify participants have correct data
    event = client.get(f"/events/{data['event_id']}", headers=auth_headers(admin_token)).json()
    all_participants = []
    for g in event["groups"]:
        all_participants.extend(g["participants"])
    assert any(p["display_name"] == "Alice" for p in all_participants)


# ── Import with extra metadata columns ──────────────────────────────────────

def test_import_csv_with_extra_columns(client: TestClient, admin_token: str):
    """Extra columns beyond standard ones are stored in metadata."""
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(CSV_WITH_METADATA), "text/csv")},
        data={"event_name": "Metadata Import"},
    )
    assert resp.status_code == 201


# ── Error cases ─────────────────────────────────────────────────────────────

def test_import_missing_required_columns(client: TestClient, admin_token: str):
    """CSV without display_name and group_name fails."""
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(MISSING_COLUMNS_CSV), "text/csv")},
        data={"event_name": "Bad Import"},
    )
    assert resp.status_code == 400


def test_import_empty_csv(client: TestClient, admin_token: str):
    """CSV with headers but no data rows fails."""
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("data.csv", io.BytesIO(EMPTY_CSV), "text/csv")},
        data={"event_name": "Empty Import"},
    )
    assert resp.status_code == 400


def test_import_non_admin_403(client: TestClient, evaluator_token: str):
    resp = client.post(
        "/events/import",
        headers=auth_headers(evaluator_token),
        files={"file": ("data.csv", io.BytesIO(STANDARD_CSV), "text/csv")},
        data={"event_name": "Nope"},
    )
    assert resp.status_code == 403
