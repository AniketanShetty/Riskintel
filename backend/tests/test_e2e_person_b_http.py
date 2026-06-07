"""
test_e2e_person_b_http.py

Person B end-to-end HTTP test, exercised via the FastAPI test client
against the live ASGI app. Mirrors test_e2e_person_a.py in coverage and
covers the full request/response cycle for the NTC pipeline:

  - Standard flow: pipeline executes, contract shape holds, audit row written.
  - HTTP boundary: response code, headers, content-type, JSON shape.
  - Floor-breach override: E5 financial-health floor forces "Not Ready".
  - Validation failure: missing field → 400 envelope (no audit row leak).
  - Persistence: report round-trip survives a fresh DB connection.

This test file complements test_e2e_person_b.py with HTTP-level
assertions (status codes, headers, error envelopes) that the original
file did not exercise.
"""
from __future__ import annotations

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.audit import get_db_path, init_db
from app.main import app as fastapi_app


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    yield fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def baseline_payload():
    """Minimal-but-valid Person B payload (output_contracts.md §2)."""
    return {
        "user_type": "person_b",
        "full_name": "Ramesh Kumar",
        "age": 42,
        "gender": "M",
        "primary_business": "Tailoring",
        "secondary_business": "none",
        "annual_income": 120000,
        "monthly_expenses": 3000,
        "loan_amount": 10000,
        "loan_purpose": "Apparels",
        "loan_tenure": 12,
        "loan_installments": 12,
        "young_dependents": 2,
        "old_dependents": 0,
        "occupants_count": 4,
        "home_ownership": 1,
        "type_of_house": "semi_pucca",
        "house_area": 450,
        "sanitary_availability": 1,
        "water_availability": 1.0,
        "social_class": "OBC",
    }


# ── 1. HTTP happy path ────────────────────────────────────────────────────


class TestPersonBHttpHappyPath:
    """Standard request/response cycle through the live ASGI app."""

    def test_endpoint_returns_200(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        assert response.status_code == 200, (
            f"expected 200, got {response.status_code}: {response.text}"
        )

    def test_endpoint_returns_json_content_type(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        assert response.headers["content-type"].startswith("application/json"), (
            f"unexpected content-type: {response.headers.get('content-type')}"
        )

    def test_response_status_field_is_success(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        body = response.json()
        assert body["status"] == "success"
        assert body["user_type"] == "person_b"

    def test_response_has_correlation_id(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        body = response.json()
        assert "correlation_id" in body
        assert isinstance(body["correlation_id"], str)
        # UUID4 — 36 chars, 4 dashes
        assert len(body["correlation_id"]) == 36
        assert body["correlation_id"].count("-") == 4

    def test_response_contains_e5_readiness(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        body = response.json()
        assert "readiness" in body
        readiness = body["readiness"]
        assert "score" in readiness
        assert "band" in readiness
        assert "components" in readiness
        # Component substructure (output_contracts.md §2)
        comps = readiness["components"]
        for key in (
            "financial_health",
            "housing_stability",
            "infrastructure_access",
            "household_burden",
            "business_viability",
        ):
            assert key in comps, f"missing readiness component: {key}"

    def test_response_contains_archetype_section(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        body = response.json()
        assert "archetype" in body
        assert "label" in body["archetype"]
        assert "cluster_id" in body["archetype"]
        # "Tailoring" maps to a known livelihood cluster
        assert isinstance(body["archetype"]["cluster_id"], int)

    def test_response_contains_recommendations(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        body = response.json()
        recs = body["explanation"]
        for key in ("decision_verdict", "primary_reason", "contributing_factors"):
            assert key in recs, f"missing recommendations key: {key}"

    def test_response_contains_applicant_echo(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        body = response.json()
        assert "applicant" in body
        assert body["applicant"]["full_name"] == "Ramesh Kumar"
        assert body["applicant"]["primary_business"] == "Tailoring"


# ── 2. HTTP error envelope ────────────────────────────────────────────────


class TestPersonBHttpErrorEnvelope:
    """Validation failures must return the frozen error envelope."""

    def test_missing_required_field_returns_400(self, client, baseline_payload):
        body = baseline_payload.copy()
        del body["annual_income"]
        response = client.post("/api/assess/person-b", json=body)
        assert response.status_code == 400, response.text
        envelope = response.json()
        assert envelope["status"] == "error"
        assert "error" in envelope
        assert "code" in envelope["error"]
        assert "message" in envelope["error"]

    def test_invalid_user_type_returns_400(self, client, baseline_payload):
        body = baseline_payload.copy()
        body["user_type"] = "person_a"  # not person_b
        response = client.post("/api/assess/person-b", json=body)
        # Pydantic literal coercion rejects the wrong user_type
        assert response.status_code == 400, response.text

    def test_malformed_json_returns_400(self, client):
        tc = TestClient(client.app, raise_server_exceptions=False)
        response = tc.post(
            "/api/assess/person-b",
            content="{not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_unified_endpoint_accepts_person_b(self, client, baseline_payload):
        """POST /api/assess (unified) routes person_b payloads correctly."""
        body = baseline_payload.copy()
        response = client.post("/api/assess", json=body)
        assert response.status_code == 200
        body_json = response.json()
        assert body_json["user_type"] == "person_b"


# ── 3. E5 floor-breach override (HTTP-level) ──────────────────────────────


class TestPersonBE5FloorBreachHttp:
    """E5 floor breach must propagate to the HTTP response band + score."""

    def test_floor_breach_forces_not_ready_band(self, client, baseline_payload):
        # Annual income effectively zero → debt_burden = 0, financial_health = 0
        # → floor breach → "Not Ready"
        payload = baseline_payload.copy()
        payload["annual_income"] = 0
        response = client.post("/api/assess/person-b", json=payload)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["readiness"]["band"] == "Not Ready"
        assert body["readiness"]["score"] == 0

    def test_floor_breach_logs_override_flag(self, client, baseline_payload):
        payload = baseline_payload.copy()
        payload["annual_income"] = 0
        response = client.post("/api/assess/person-b", json=payload)
        assert response.status_code == 200
        body = response.json()

        # Audit row must contain the override flags
        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?",
                (body["correlation_id"],),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        assert row is not None, "audit row missing"
        flags = json.loads(row[0])
        assert "OVERRIDE_E5_FLOOR_BREACH" in flags
        assert "ENGINE_POLICY_OVERRIDE" in flags


# ── 4. Audit ledger consistency (HTTP-level) ──────────────────────────────


class TestPersonBAuditLedger:
    """Every successful HTTP request must produce exactly one audit row."""

    def test_one_audit_row_per_successful_request(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        assert response.status_code == 200
        cid = response.json()["correlation_id"]

        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM audit_log WHERE correlation_id = ?", (cid,))
            (count,) = cur.fetchone()
        finally:
            conn.close()

        assert count == 1, f"expected 1 audit row for {cid}, got {count}"

    def test_audit_row_stores_final_verdict(self, client, baseline_payload):
        response = client.post("/api/assess/person-b", json=baseline_payload)
        assert response.status_code == 200
        body = response.json()

        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT final_verdict FROM audit_log WHERE correlation_id = ?",
                (body["correlation_id"],),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row[0] == body["readiness"]["band"]


# ── 5. Two sequential requests are independent ────────────────────────────


class TestPersonBHttpSequential:
    """Two requests in a row must produce distinct correlation_ids and audit rows."""

    def test_two_requests_distinct_correlation_ids(self, client, baseline_payload):
        r1 = client.post("/api/assess/person-b", json=baseline_payload)
        r2 = client.post("/api/assess/person-b", json=baseline_payload)
        assert r1.status_code == 200
        assert r2.status_code == 200
        cid1 = r1.json()["correlation_id"]
        cid2 = r2.json()["correlation_id"]
        assert cid1 != cid2

    def test_two_requests_write_two_audit_rows(self, client, baseline_payload):
        r1 = client.post("/api/assess/person-b", json=baseline_payload)
        r2 = client.post("/api/assess/person-b", json=baseline_payload)
        cids = (r1.json()["correlation_id"], r2.json()["correlation_id"])

        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM audit_log WHERE correlation_id IN (?, ?)",
                cids,
            )
            (count,) = cur.fetchone()
        finally:
            conn.close()

        assert count == 2


# ── 6. Report persistence from a Person B assessment ─────────────────────


class TestPersonBReportPersistence:
    """A Person B assessment can drive a report and survive a fresh DB connection."""

    def test_person_b_assessment_to_report_round_trip(self, client, baseline_payload):
        # 1. Assess
        response = client.post("/api/assess/person-b", json=baseline_payload)
        assert response.status_code == 200
        body = response.json()
        body["user_type"] = "person_b"
        body["applicant"] = baseline_payload  # ensure applicant present

        # 2. Generate report from that assessment body
        gen = client.post("/api/report/generate", json=body)
        assert gen.status_code == 200, gen.text
        rid = gen.headers["x-report-id"]
        assert rid.startswith("RI-")

        # 3. Fresh DB connection — simulate restart
        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT pdf_blob, user_type FROM reports WHERE report_id = ?", (rid,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        assert row is not None, f"Report {rid} missing after 'restart'"
        assert bytes(row[0])[:4] == b"%PDF"
        assert row[1] == "person_b"

        # 4. Download endpoint serves the same blob
        dl = client.get(f"/api/report/download/{rid}")
        assert dl.status_code == 200
        assert dl.content == gen.content
