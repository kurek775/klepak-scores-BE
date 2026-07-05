"""Tests for POST /events/{id}/bootstrap-evaluators — auto-mint one evaluator per group."""

import io

from fastapi.testclient import TestClient

from app.core.text import slugify
from tests.conftest import auth_headers

CSV = b"display_name,group_name\nAlice,1.oddil\nBob,2.oddil\n"


def _import_event(client: TestClient, token: str, name: str = "Letni tabor 2026") -> int:
    return client.post(
        "/events/import",
        headers=auth_headers(token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": name},
    ).json()["event_id"]


def test_bootstrap_creates_one_evaluator_per_group(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.post(f"/events/{event_id}/bootstrap-evaluators", headers=auth_headers(admin_token))
    assert resp.status_code == 201
    data = resp.json()

    assert len(data["created"]) == 2
    assert data["skipped_groups"] == []

    # unique emails, shared password = event name, diacritic- and space-free
    emails = {c["email"] for c in data["created"]}
    assert len(emails) == 2
    assert all(c["password"] == "Letnitabor2026" for c in data["created"])
    assert all(" " not in c["password"] for c in data["created"])

    # emails are clean — plain group@event.cz with no random suffix
    for c in data["created"]:
        assert c["email"] == f"{slugify(c['group_name'])}@{slugify('Letni tabor 2026')}.cz"

    # full_name reads as the team's leader, e.g. "Vedoucí 1.oddil"
    assert all(c["full_name"] == f"Vedoucí {c['group_name']}" for c in data["created"])

    # the event pool now holds both auto-created evaluators
    pool = client.get(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token)).json()
    assert len(pool) == 2


def test_bootstrap_email_disambiguates_same_named_events_with_event_id(
    client: TestClient, admin_token: str
):
    """A second event with the same name reuses the domain, so emails clash;
    they are disambiguated with the event id — never a random suffix."""
    e1 = _import_event(client, admin_token, name="Duplicate Camp")
    client.post(f"/events/{e1}/bootstrap-evaluators", headers=auth_headers(admin_token))

    e2 = _import_event(client, admin_token, name="Duplicate Camp")
    data = client.post(
        f"/events/{e2}/bootstrap-evaluators", headers=auth_headers(admin_token)
    ).json()

    for c in data["created"]:
        assert c["email"].endswith("@duplicate-camp.cz")
        assert f"-{e2}@" in c["email"]  # event id, not a random hex


def test_bootstrap_password_strips_diacritics_and_whitespace(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token, name="Letní tábor 2026")
    data = client.post(
        f"/events/{event_id}/bootstrap-evaluators", headers=auth_headers(admin_token)
    ).json()
    assert data["created"][0]["password"] == "Letnitabor2026"


def test_bootstrap_credentials_login_and_are_group_scoped(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    created = client.post(
        f"/events/{event_id}/bootstrap-evaluators", headers=auth_headers(admin_token)
    ).json()["created"]
    cred = created[0]

    # generated login works immediately (active, no invite step)
    login = client.post("/auth/login", json={"email": cred["email"], "password": cred["password"]})
    assert login.status_code == 200
    token = login.json()["access_token"]

    # the evaluator sees exactly their own single group
    mine = client.get("/groups/my-groups", headers=auth_headers(token)).json()
    assert len(mine) == 1
    assert mine[0]["name"] == cred["group_name"]


def test_bootstrap_is_idempotent(client: TestClient, admin_token: str):
    event_id = _import_event(client, admin_token)
    client.post(f"/events/{event_id}/bootstrap-evaluators", headers=auth_headers(admin_token))

    # second run creates nothing; both groups already covered
    resp = client.post(f"/events/{event_id}/bootstrap-evaluators", headers=auth_headers(admin_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == []
    assert len(data["skipped_groups"]) == 2

    pool = client.get(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token)).json()
    assert len(pool) == 2


def test_bootstrap_non_admin_403(client: TestClient, admin_token: str, evaluator_token: str):
    event_id = _import_event(client, admin_token)
    resp = client.post(
        f"/events/{event_id}/bootstrap-evaluators", headers=auth_headers(evaluator_token)
    )
    assert resp.status_code == 403


def test_bootstrap_event_not_found_404(client: TestClient, admin_token: str):
    resp = client.post("/events/9999/bootstrap-evaluators", headers=auth_headers(admin_token))
    assert resp.status_code == 404


# ── One-call import + bootstrap (?bootstrap=true) ────────────────────────────

def test_import_with_bootstrap_flag_mints_evaluators(client: TestClient, admin_token: str):
    resp = client.post(
        "/events/import?bootstrap=true",
        headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "Letni tabor 2026"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["groups_created"] == 2
    assert len(data["evaluators"]) == 2

    # credentials returned by the import work immediately
    cred = data["evaluators"][0]
    login = client.post("/auth/login", json={"email": cred["email"], "password": cred["password"]})
    assert login.status_code == 200


def test_import_without_bootstrap_flag_mints_nothing(client: TestClient, admin_token: str):
    resp = client.post(
        "/events/import",
        headers=auth_headers(admin_token),
        files={"file": ("p.csv", io.BytesIO(CSV), "text/csv")},
        data={"event_name": "No Bootstrap"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["evaluators"] == []

    event_id = data["event_id"]
    pool = client.get(f"/events/{event_id}/evaluators", headers=auth_headers(admin_token)).json()
    assert pool == []
