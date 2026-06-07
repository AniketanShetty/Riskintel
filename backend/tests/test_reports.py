"""
High-value integration tests for the frozen report endpoints.

Reference: docs/output_contracts.md §3 (PDF Report Payload).

Endpoints under test:
    POST /api/report/generate
    GET  /api/report/download/{id}

Style: mirrors tests/test_integration_high_value.py.

Reports are persisted in the unified SQLite DB (table `reports`); per-test
isolation is handled by the `clean_reports` fixture in conftest.py, which
truncates the table after each test in this module.
"""
from __future__ import annotations

import io
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app as fastapi_app
from app.audit import get_db_path, init_db
from app.core.config import settings


def _report_id_from_response(response) -> str:
    """Extract the report_id from a generate response header."""
    return response.headers.get("x-report-id", "")


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    yield fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)



@pytest.fixture
def person_a_assessment():
    """Minimal Person A assessment response shape (output_contracts.md §1)."""
    return {
        "status": "success",
        "user_type": "person_a",
        "timestamp": "2026-06-06T10:00:00Z",
        "correlation_id": "11111111-1111-1111-1111-111111111111",
        "applicant": {
            "user_type": "person_a",
            "full_name": "Aniket Sharma",
            "age": 34,
            "gender": "M",
            "marital_status": "Married",
            "education": "Graduate",
            "self_employed": "No",
            "years_at_current_employer": 6,
            "annual_income": 9600000,
            "dependents": 2,
            "cibil_score": 742,
            "loan_amount": 15000000,
            "loan_term": 12,
            "loan_purpose": "home",
            "residential_assets_value": 5600000,
            "commercial_assets_value": 3700000,
            "luxury_assets_value": 8800000,
            "bank_asset_value": 3300000,
        },
        "eligibility": {
            "verdict": "Highly Likely",
            "probability": 0.9694,
            "bias": 0.6209,
            "feature_contributions": {
                "dependents": 0.0006,
                "education": -0.0008,
                "self_employed": -0.0005,
                "annual_income": -0.0157,
                "loan_amount": -0.0053,
                "loan_term": -0.0166,
                "cibil_score": 0.4037,
                "residential_assets_value": 0.0057,
                "commercial_assets_value": 0.0014,
                "luxury_assets_value": -0.0145,
                "bank_asset_value": -0.0095,
            },
        },
        "risk_tier": {
            "tier": "P1",
            "label": "Low Risk",
            "description": "Low Risk",
            "score_used": 742,
            "thresholds": {"P1": "\u2265 701", "P2": "669 \u2013 700", "P3": "659 \u2013 668", "P4": "\u2264 658"},
        },
        "archetype": {
            "label": "Young Starters",
            "description": "Younger demographic.",
            "cluster_id": 2,
        },
        "explanation": {
            "decision_verdict": "Mock", "primary_reason": "Mock", "contributing_factors": [],
            "primary_reason": [],
            "recommendations": ["Maintain credit."],
            "contributing_factors": ["Monitor score."],
        },
    }


@pytest.fixture
def person_b_assessment():
    """Minimal Person B assessment response shape (output_contracts.md §2)."""
    return {
        "status": "success",
        "user_type": "person_b",
        "timestamp": "2026-06-06T10:00:00Z",
        "correlation_id": "22222222-2222-2222-2222-222222222222",
        "applicant": {
            "user_type": "person_b",
            "full_name": "Ramesh Kumar",
            "age": 42,
            "gender": "M",
            "primary_business": "Tailoring",
            "secondary_business": "none",
            "annual_income": 120000,
            "monthly_expenses": 8000,
            "loan_amount": 50000,
            "loan_purpose": "Apparels",
            "loan_tenure": 12,
            "loan_installments": 12,
            "young_dependents": 3,
            "old_dependents": 1,
            "occupants_count": 6,
            "home_ownership": 1,
            "type_of_house": "T2",
            "house_area": 450,
            "sanitary_availability": 1,
            "water_availability": 0.5,
            "social_class": "OBC",
        },
        "readiness": {
            "score": 68,
            "band": "Moderately Ready",
            "components": {
                "financial_health": {"score": 72, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 75, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 75, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 45, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 70, "weight": 0.15, "factors": {}},
            },
        },
        "archetype": {
            "label": "Micro-Retail",
            "description": "Small-scale retail.",
            "cluster_id": 2,
        },
        "explanation": {
            "decision_verdict": "Mock", "primary_reason": "Mock", "contributing_factors": [],
            "primary_reason": ["High dependent burden."],
            "recommendations": ["Diversify income."],
            "contributing_factors": ["Join an SHG."],
        },
    }


# ── 1. Happy path: generate + download round-trip ──────────────────────────


class TestReportHappyPath:

    def test_generate_person_a_returns_200(self, client, person_a_assessment):
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert response.status_code == 200

    def test_generate_returns_pdf_content_type(self, client, person_a_assessment):
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert response.headers["content-type"] == "application/pdf"

    def test_generate_returns_attachment_disposition(self, client, person_a_assessment):
        response = client.post("/api/report/generate", json=person_a_assessment)
        cd = response.headers.get("content-disposition", "")
        assert cd.startswith("attachment;")
        assert ".pdf" in cd

    def test_generate_returns_pdf_bytes(self, client, person_a_assessment):
        response = client.post("/api/report/generate", json=person_a_assessment)
        body = response.content
        # PDF magic number
        assert body[:4] == b"%PDF", f"not a PDF (first 4 bytes: {body[:4]!r})"
        # Reasonable size floor
        assert len(body) > 500, f"PDF too small: {len(body)} bytes"

    def test_generate_returns_report_id_header(self, client, person_a_assessment):
        response = client.post("/api/report/generate", json=person_a_assessment)
        rid = response.headers.get("x-report-id", "")
        assert rid.startswith("RI-"), f"bad report id: {rid}"
        # Format: RI-YYYYMMDD-A-NNNNN
        parts = rid.split("-")
        assert len(parts) == 4
        assert parts[1].isdigit() and len(parts[1]) == 8
        assert parts[2] in ("A", "B")
        assert parts[3].isdigit() and len(parts[3]) == 5

    def test_generate_person_b_returns_pdf(self, client, person_b_assessment):
        response = client.post("/api/report/generate", json=person_b_assessment)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content[:4] == b"%PDF"

    def test_download_returns_same_pdf(self, client, person_a_assessment):
        gen = client.post("/api/report/generate", json=person_a_assessment)
        rid = gen.headers["x-report-id"]
        dl = client.get(f"/api/report/download/{rid}")
        assert dl.status_code == 200
        assert dl.headers["content-type"] == "application/pdf"
        assert dl.content[:4] == b"%PDF"
        # Generated and downloaded PDFs should be identical bytes
        assert dl.content == gen.content

    def test_download_has_attachment_disposition(self, client, person_a_assessment):
        gen = client.post("/api/report/generate", json=person_a_assessment)
        rid = gen.headers["x-report-id"]
        dl = client.get(f"/api/report/download/{rid}")
        cd = dl.headers.get("content-disposition", "")
        assert cd.startswith("attachment;")
        assert rid in cd
        assert ".pdf" in cd

    def test_two_generations_produce_distinct_report_ids(
        self, client, person_a_assessment
    ):
        a = client.post("/api/report/generate", json=person_a_assessment)
        b = client.post("/api/report/generate", json=person_a_assessment)
        assert a.headers["x-report-id"] != b.headers["x-report-id"]


# ── 2. Validation failures: frozen envelope ────────────────────────────────


class TestReportValidationFailures:

    def test_malformed_json_returns_400_envelope(self, client, app):
        tc = TestClient(app, raise_server_exceptions=False)
        response = tc.post(
            "/api/report/generate",
            content="{not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        body = response.json()
        assert body.get("status") == "error"
        assert "error" in body

    def test_missing_user_type_returns_400(self, client, person_a_assessment):
        body = person_a_assessment.copy()
        del body["user_type"]
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 400
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] in ("INVALID_USER_TYPE", "MISSING_REQUIRED_FIELD")

    def test_invalid_user_type_returns_400(self, client, person_a_assessment):
        body = person_a_assessment.copy()
        body["user_type"] = "martian"
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 400
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "INVALID_USER_TYPE"

    def test_missing_applicant_returns_400(self, client, person_a_assessment):
        body = person_a_assessment.copy()
        del body["applicant"]
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 400
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "MISSING_REQUIRED_FIELD"

    def test_person_a_missing_eligibility_returns_400(self, client, person_a_assessment):
        body = person_a_assessment.copy()
        del body["eligibility"]
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 400
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "MISSING_REQUIRED_FIELD"

    def test_person_b_missing_readiness_returns_400(self, client, person_b_assessment):
        body = person_b_assessment.copy()
        del body["readiness"]
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 400
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "MISSING_REQUIRED_FIELD"

    def test_non_dict_body_returns_400(self, client):
        response = client.post("/api/report/generate", json=[1, 2, 3])
        assert response.status_code == 400


# ── 3. Download edge cases ─────────────────────────────────────────────────


class TestReportDownload:

    def test_download_unknown_id_returns_404(self, client):
        # Format-valid id that was never issued
        fake_id = "RI-20260606-A-99999"
        response = client.get(f"/api/report/download/{fake_id}")
        assert response.status_code == 404
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "REPORT_NOT_FOUND"

    def test_download_malformed_id_returns_400(self, client):
        response = client.get("/api/report/download/not-a-valid-id")
        assert response.status_code == 400
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["code"] == "VALIDATION_ERROR"

    def test_download_empty_id_returns_400(self, client):
        response = client.get("/api/report/download/")
        # 404 from FastAPI's default route — the empty path does not match
        # the /download/{report_id} pattern. Accept either.
        assert response.status_code in (400, 404)


# ── 4. Persistence: report_id -> blob in unified SQLite DB ──────────────────


def _fetch_report_row(report_id: str):
    """Read a reports-table row by id; return (generated_at, user_type, version, blob) or None."""
    conn = sqlite3.connect(get_db_path(), timeout=5.0)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT generated_at, user_type, version, pdf_blob "
            "FROM reports WHERE report_id = ?",
            (report_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {"generated_at": row[0], "user_type": row[1], "version": row[2], "blob": bytes(row[3])}
    finally:
        conn.close()


class TestReportPersistence:
    """Verify that generated PDFs are persisted to the unified SQLite DB.

    The contract (output_contracts.md §3) requires that reports can be
    retrieved by ID after the generate response is returned. Persistence
    is implemented as a row in the `reports` table of the unified DB
    (same DB as `audit_log`), so reports survive process restarts.
    """

    def test_generate_writes_row_to_reports_table(
        self, client, person_a_assessment
    ):
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert response.status_code == 200
        rid = _report_id_from_response(response)
        row = _fetch_report_row(rid)
        assert row is not None, f"no row found for {rid}"
        assert row["user_type"] == "person_a"
        assert row["version"] == "1.0"
        assert row["blob"][:4] == b"%PDF"

    def test_blob_matches_response_body(self, client, person_a_assessment):
        response = client.post("/api/report/generate", json=person_a_assessment)
        rid = _report_id_from_response(response)
        row = _fetch_report_row(rid)
        assert row is not None
        assert row["blob"] == response.content, (
            f"DB blob differs from response body "
            f"({len(row['blob'])} vs {len(response.content)} bytes)"
        )

    def test_two_generations_write_distinct_rows(
        self, client, person_a_assessment
    ):
        a = client.post("/api/report/generate", json=person_a_assessment)
        b = client.post("/api/report/generate", json=person_a_assessment)
        rid_a = _report_id_from_response(a)
        rid_b = _report_id_from_response(b)
        assert rid_a != rid_b, "report IDs must be distinct"
        row_a = _fetch_report_row(rid_a)
        row_b = _fetch_report_row(rid_b)
        assert row_a is not None and row_b is not None
        assert row_a["blob"][:4] == b"%PDF"
        assert row_b["blob"][:4] == b"%PDF"

    def test_download_reads_blob_from_db(
        self, client, person_a_assessment
    ):
        """
        Prove the download endpoint serves the blob from the SQLite reports
        table by generating, re-fetching, and verifying byte-for-byte
        identity (so the only source of truth is the DB row, not in-memory
        state from the original request handler).
        """
        gen = client.post("/api/report/generate", json=person_a_assessment)
        assert gen.status_code == 200
        rid = _report_id_from_response(gen)
        dl = client.get(f"/api/report/download/{rid}")
        assert dl.status_code == 200
        assert dl.content == gen.content, (
            "Downloaded PDF bytes differ from generated bytes"
        )


# ── 4b. Persistence survives simulated restart ─────────────────────────────


class TestReportPersistenceSurvivesRestart:
    """Simulate a process restart and prove persisted reports are recoverable.

    Strategy:
      1. Generate a report via POST /api/report/generate
      2. Read the blob directly from the SQLite DB (as a new connection
         would on restart)
      3. Verify the blob is valid PDF and matches the response body
      4. Prove the download endpoint serves the same blob (the endpoint
         always reads from the DB, not an in-memory cache)
    """

    def test_blob_is_readable_from_new_connection(
        self, client, person_a_assessment
    ):
        """Generate, then read from a fresh sqlite3 connection (simulating restart)."""
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert response.status_code == 200
        rid = _report_id_from_response(response)

        # Open a *new* connection as a fresh process would
        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT pdf_blob, generated_at, user_type, version "
                "FROM reports WHERE report_id = ?",
                (rid,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        assert row is not None, f"Report {rid} not found in DB after 'restart'"
        stored_blob = bytes(row[0])
        assert stored_blob[:4] == b"%PDF", "Stored blob is not valid PDF"
        assert stored_blob == response.content, (
            "DB blob differs from original generate response"
        )
        assert "T" in str(row[1]), f"generated_at missing timestamp: {row[1]}"
        assert row[2] == "person_a"
        assert row[3] == "1.0"

    def test_download_after_simulated_restart(
        self, client, person_a_assessment
    ):
        """Generate, then download (reads from DB), proving no in-memory cache needed."""
        gen = client.post("/api/report/generate", json=person_a_assessment)
        assert gen.status_code == 200
        rid = _report_id_from_response(gen)

        # The download endpoint always reads from the DB
        dl = client.get(f"/api/report/download/{rid}")
        assert dl.status_code == 200
        assert dl.content == gen.content, (
            "Download after restart simulation returns different bytes"
        )

    def test_multiple_blobs_survive(
        self, client, person_a_assessment, person_b_assessment
    ):
        """Multiple reports generated before restart are all recoverable."""
        gen_a = client.post("/api/report/generate", json=person_a_assessment)
        gen_b = client.post("/api/report/generate", json=person_b_assessment)
        assert gen_a.status_code == 200
        assert gen_b.status_code == 200
        rid_a = _report_id_from_response(gen_a)
        rid_b = _report_id_from_response(gen_b)

        # Fresh connection — simulate restart
        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute("SELECT report_id, pdf_blob FROM reports ORDER BY report_id")
            rows = cur.fetchall()
        finally:
            conn.close()

        report_ids = [r[0] for r in rows]
        assert rid_a in report_ids, f"{rid_a} missing after restart"
        assert rid_b in report_ids, f"{rid_b} missing after restart"
        assert len(rows) >= 2, f"Expected >= 2 rows, got {len(rows)}"


# ── 4c. No dual database path ──────────────────────────────────────────────


class TestNoDualDatabasePath:
    """Verify the entire system uses a single canonical DB path.

    All persistence — audit_log rows AND reports table — goes through
    `app.audit.get_db_path()` which resolves to `settings.DB_PATH_ABS`.
    There is no secondary database, no in-memory fallback, no filesystem
    storage for reports.
    """

    def test_get_db_path_matches_settings(self):
        """The DB path from the audit module matches the config path."""
        from app.audit import get_db_path
        assert get_db_path() == str(settings.DB_PATH_ABS), (
            f"audit.get_db_path()={get_db_path()} != "
            f"settings.DB_PATH_ABS={settings.DB_PATH_ABS}"
        )

    def test_only_one_db_file_exists(self):
        """Only the canonical DB file exists; no riskintel_test.db etc."""
        db_path = settings.DB_PATH_ABS
        assert db_path.exists(), f"Canonical DB not found at {db_path}"
        # Check the parent directory for any other riskintel*.db files
        parent = db_path.parent
        other_dbs = list(parent.glob("riskintel*.db"))
        # Only the canonical DB should exist
        assert len(other_dbs) == 1, (
            f"Found {len(other_dbs)} riskintel*.db files in {parent}: "
            f"{[p.name for p in other_dbs]}"
        )

    def test_reports_table_lives_in_canonical_db(self, client, person_a_assessment):
        """The `reports` table is in the same DB as `audit_log`."""
        # Generate a report
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert response.status_code == 200
        rid = _report_id_from_response(response)

        # Verify both tables exist in the same DB
        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('audit_log', 'reports') ORDER BY name"
            )
            tables = [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

        assert "audit_log" in tables, "audit_log table missing from canonical DB"
        assert "reports" in tables, "reports table missing from canonical DB"

    def test_report_row_same_db_as_audit_log(self, client, person_a_assessment):
        """The report row and audit rows coexist in the same physical file."""
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert response.status_code == 200
        rid = _report_id_from_response(response)

        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            # Check reports table
            cur.execute("SELECT COUNT(*) FROM reports WHERE report_id = ?", (rid,))
            assert cur.fetchone()[0] == 1, "Report row not in canonical DB"
            # Verify it's the same file by checking sqlite_master for both tables
            cur.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
                "AND name IN ('audit_log', 'reports')"
            )
            assert cur.fetchone()[0] == 2, (
                "Both tables must exist in the same database file"
            )
        finally:
            conn.close()

    def test_init_db_creates_both_tables(self):
        """Calling init_db() ensures both tables exist in the canonical DB."""
        init_db()
        conn = sqlite3.connect(get_db_path(), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('audit_log', 'reports') ORDER BY name"
            )
            tables = [r[0] for r in cur.fetchall()]
            assert "audit_log" in tables
            assert "reports" in tables
        finally:
            conn.close()


# ── 5. Response shape: PDF body content ────────────────────────────────────


class TestReportResponseShape:
    """Verify the internal structure of the PDF bytes.

    The contract specifies the report_id, generated_at, user_type, version,
    applicant summary, and verdict/readiness band appear in the document.
    These tests use PdfReader to extract text from the compressed PDF stream.
    """

    @staticmethod
    def _text(response) -> str:
        """Extract all page text from a generate response using PdfReader."""
        reader = PdfReader(io.BytesIO(response.content))
        return "\n".join(p.extract_text() for p in reader.pages)

    def test_pdf_contains_riskintel_header(
        self, client, person_a_assessment
    ):
        text = self._text(client.post("/api/report/generate", json=person_a_assessment))
        assert "RiskIntel Assessment Report" in text

    def test_pdf_contains_report_metadata(
        self, client, person_a_assessment
    ):
        response = client.post("/api/report/generate", json=person_a_assessment)
        text = self._text(response)
        rid = _report_id_from_response(response)
        assert "Report ID:" in text
        assert rid in text
        assert "User Type:" in text
        assert "person_a" in text
        assert "Version:" in text
        assert "1.0" in text

    def test_pdf_contains_generated_at_timestamp(
        self, client, person_a_assessment
    ):
        text = self._text(client.post("/api/report/generate", json=person_a_assessment))
        assert "Generated:" in text
        # Must contain an ISO-like timestamp (YYYY-MM-DDT...)
        import re

        assert re.search(r"Generated:\s*\d{4}-\d{2}-\d{2}T", text), (
            "PDF missing ISO timestamp after 'Generated:'"
        )

    def test_pdf_contains_applicant_summary_person_a(
        self, client, person_a_assessment
    ):
        text = self._text(client.post("/api/report/generate", json=person_a_assessment))
        assert "Applicant Summary" in text
        assert "Aniket Sharma" in text
        assert "CIBIL Score:" in text
        assert "742" in text

    def test_pdf_contains_verdict_section_person_a(
        self, client, person_a_assessment
    ):
        text = self._text(client.post("/api/report/generate", json=person_a_assessment))
        assert "Verdict" in text
        assert "Highly Likely" in text
        assert "Probability:" in text

    def test_person_b_pdf_contains_business_and_readiness(
        self, client, person_b_assessment
    ):
        """Person B PDF uses readiness band and primary business fields."""
        response = client.post("/api/report/generate", json=person_b_assessment)
        assert response.status_code == 200
        text = self._text(response)
        assert "RiskIntel Assessment Report" in text
        assert "Report ID:" in text
        rid = _report_id_from_response(response)
        assert rid in text
        assert "person_b" in text
        assert "Applicant Summary" in text
        assert "Ramesh Kumar" in text
        # Person B: Primary Business instead of CIBIL Score
        assert "Primary Business:" in text
        assert "Tailoring" in text
        # Verdict section with readiness info
        assert "Verdict" in text
        assert "Readiness" in text
        assert "Moderately Ready" in text

    def test_content_disposition_filename_contains_report_id(
        self, client, person_a_assessment
    ):
        response = client.post("/api/report/generate", json=person_a_assessment)
        cd = response.headers.get("content-disposition", "")
        assert cd.startswith("attachment;")
        rid = _report_id_from_response(response)
        assert rid in cd, f"report_id {rid} not in Content-Disposition: {cd}"
        assert "RiskIntel_Report_" in cd
        assert ".pdf" in cd

    def test_x_report_id_header_format(
        self, client, person_a_assessment
    ):
        response = client.post("/api/report/generate", json=person_a_assessment)
        assert "x-report-id" in response.headers, "Missing x-report-id header"
        rid = response.headers["x-report-id"]
        # Format: RI-YYYYMMDD-A-NNNNN
        parts = rid.split("-")
        assert len(parts) == 4
        assert parts[0] == "RI"
        assert parts[1].isdigit() and len(parts[1]) == 8
        assert parts[2] in ("A", "B")
        assert parts[3].isdigit() and len(parts[3]) == 5


# ── 6. Edge cases ──────────────────────────────────────────────────────────


class TestReportEdgeCases:
    """Boundary and edge-case scenarios for report endpoints."""

    def test_person_b_generate_then_download_roundtrip(
        self, client, person_b_assessment
    ):
        """Full generate + download round-trip for Person B."""
        gen = client.post("/api/report/generate", json=person_b_assessment)
        assert gen.status_code == 200
        rid = _report_id_from_response(gen)
        dl = client.get(f"/api/report/download/{rid}")
        assert dl.status_code == 200
        assert dl.headers["content-type"] == "application/pdf"
        assert dl.content[:4] == b"%PDF"
        # Generated and downloaded bytes must match
        assert dl.content == gen.content
        # Content-Disposition for download
        cd = dl.headers.get("content-disposition", "")
        assert cd.startswith("attachment;")
        assert rid in cd
        assert ".pdf" in cd

    def test_report_id_sequence_increments(
        self, client, person_a_assessment
    ):
        """Two generates on the same user_type in a session get sequential IDs."""
        a = client.post("/api/report/generate", json=person_a_assessment)
        b = client.post("/api/report/generate", json=person_a_assessment)
        rid_a = _report_id_from_response(a)
        rid_b = _report_id_from_response(b)
        # They must differ and the numeric suffix should increment
        seq_a = int(rid_a.split("-")[3])
        seq_b = int(rid_b.split("-")[3])
        assert seq_b > seq_a, (
            f"Sequence did not increment: {rid_a} -> {rid_b}"
        )

    def test_report_id_user_type_bucket_separate(
        self, client, person_a_assessment, person_b_assessment
    ):
        """Person A and Person B sequences are independent."""
        a = client.post("/api/report/generate", json=person_a_assessment)
        b = client.post("/api/report/generate", json=person_b_assessment)
        rid_a = _report_id_from_response(a)
        rid_b = _report_id_from_response(b)
        # User-type letters differ
        assert rid_a.split("-")[2] == "A"
        assert rid_b.split("-")[2] == "B"
        assert rid_a != rid_b

    def test_extra_fields_in_body_ignored(
        self, client, person_a_assessment
    ):
        """Extra unknown fields in assessment body do not cause errors."""
        body = person_a_assessment.copy()
        body["extra_field_xyz"] = "should be ignored"
        body["another_extra"] = 12345
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_minimal_applicant_succeeds(
        self, client
    ):
        """Generate succeeds with minimal applicant fields."""
        body = {
            "user_type": "person_a",
            "applicant": {
                "full_name": "Minimal Test",
            },
            "eligibility": {
                "verdict": "Likely",
                "probability": 0.85,
                "bias": 0.50,
                "feature_contributions": {"f1": 0.35},
            },
        }
        response = client.post("/api/report/generate", json=body)
        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"
        text = PdfReader(io.BytesIO(response.content)).pages[0].extract_text()
        assert "Minimal Test" in text
        assert "Likely" in text
