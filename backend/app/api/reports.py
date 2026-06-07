"""
Report endpoints — frozen contract surface (output_contracts.md §3).

Endpoints (mounted under /api):
    POST /api/report/generate         — body: full assessment response; returns PDF binary
    GET  /api/report/download/{id}   — returns PDF binary by report_id

PDF metadata per contract:
    report_id     = RI-YYYYMMDD-{A|B}-{5-digit}
    generated_at  = ISO 8601
    user_type     = "person_a" | "person_b"
    version       = "1.0"

Response headers (per contract):
    Content-Type:        application/pdf
    Content-Disposition: attachment; filename="RiskIntel_Report_{report_id}.pdf"

Persistence:
    PDF bytes and the daily sequence are stored in the same SQLite database
    as the audit log (single canonical persistence path; survives process
    restarts). No on-disk PDF files. The reports table is initialized by
    app.audit.init_db().
"""
from __future__ import annotations

import io
import logging
import re
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.audit import get_db_path, init_db
from app.core.config import settings
from app.schemas.common import ErrorBody, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])

# Process-local locks; coordination across workers is via the SQLite engine.
_REGISTRY_LOCK = threading.Lock()
_SEQUENCE_LOCK = threading.Lock()

# report_id format: RI-YYYYMMDD-{A|B}-NNNNN (length 19, indices 0-18)
_REPORT_ID_PATTERN = re.compile(r"^RI-(\d{8})-([AB])-(\d{5})$")



def _error(status_code: int, code: str, message: str) -> JSONResponse:
    """Frozen error envelope (matches assess route)."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorBody(code=code, message=message),
        ).model_dump(),
    )


# ── SQLite-backed persistence ──────────────────────────────────────────────


def _db_conn() -> sqlite3.Connection:
    """Open a sqlite3 connection to the unified audit DB. Caller closes."""
    init_db()  # ensures both `audit_log` and `reports` tables exist
    return sqlite3.connect(get_db_path(), timeout=5.0)


def _build_report_id(user_type: str) -> str:
    """Mint the next report_id for (day, user_type).

    Sequence strategy (DB is authoritative):
      seq = db_max + 1  for the day bucket

    The DB `reports` table is the single source of truth for the next
    sequence number. The in-process `_PROCESS_SEQUENCE` cache is
    updated as a side-effect only — it is never consulted to decide the
    next id, so a missing or stale cache cannot cause collisions.

    The table's PRIMARY KEY on `report_id` is the final guard: if two
    processes race to insert the same id, the second raises an
    `IntegrityError` and the request fails loudly (no silent overwrite).
    """
    assert user_type in ("person_a", "person_b")
    day_key = datetime.now(timezone.utc).strftime("%Y%m%d")
    letter = "A" if user_type == "person_a" else "B"
    bucket = f"{day_key}-{letter}"
    with _SEQUENCE_LOCK:
        # DB-side maximum for the day bucket — sole source of truth
        conn = _db_conn()
        try:
            cur = conn.cursor()
            # report_id format: "RI-YYYYMMDD-{A|B}-NNNNN" (length 19).
            # Positions (1-based):
            #   R(1) I(2) -(3) Y(4)..Y(11) -(12) A(13) -(14) N(15)..N(19)
            # Letter at pos 13, 5-digit sequence at pos 15..19.
            # The previous offsets (12, 14) mis-extracted a dash and the
            # letter, causing CAST to return 0 every time and silently
            # minting duplicate ids across restarts.
            cur.execute(
                "SELECT MAX(CAST(substr(report_id, 15, 5) AS INTEGER)) "
                "FROM reports WHERE report_id LIKE ? AND substr(report_id, 13, 1) = ?",
                (f"RI-{day_key}-%", letter),
            )
            row = cur.fetchone()
            db_max = int(row[0]) if row and row[0] is not None else 0
        finally:
            conn.close()
        seq = db_max + 1
    return f"RI-{day_key}-{letter}-{seq:05d}"


def _store_report(report_id: str, generated_at: str, user_type: str, version: str, pdf_bytes: bytes) -> None:
    conn = _db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reports (report_id, generated_at, user_type, version, pdf_blob) "
            "VALUES (?, ?, ?, ?, ?)",
            (report_id, generated_at, user_type, version, pdf_bytes),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        # The DB is the source of truth for report_id uniqueness.
        # If the PRIMARY KEY constraint fires here it means two
        # processes raced to mint the same id — surface it loudly so
        # the caller sees a 500, not a silent overwrite.
        logger.error(
            "report_id collision detected (DB is authoritative): %s — %s",
            report_id, exc,
        )
        raise
    finally:
        conn.close()


def _fetch_report_blob(report_id: str) -> Optional[bytes]:
    conn = _db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT pdf_blob FROM reports WHERE report_id = ?", (report_id,))
        row = cur.fetchone()
        if row is None:
            return None
        # sqlite3 returns BLOB as bytes
        return bytes(row[0])
    finally:
        conn.close()


# ── PDF rendering ──────────────────────────────────────────────────────────


def _render_pdf(assessment: Dict[str, Any], metadata: Dict[str, Any]) -> bytes:
    """Render a minimal but contract-shaped PDF for the given assessment."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "RiskIntel Assessment Report")
    c.setFont("Helvetica", 10)
    c.drawString(72, height - 92, f"Report ID: {metadata['report_id']}")
    c.drawString(72, height - 106, f"Generated: {metadata['generated_at']}")
    c.drawString(72, height - 120, f"User Type: {metadata['user_type']}")
    c.drawString(72, height - 134, f"Version:   {metadata['version']}")

    # Applicant summary
    y = height - 170
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Applicant Summary")
    y -= 18
    c.setFont("Helvetica", 10)
    applicant = assessment.get("applicant") or {}
    full_name = applicant.get("full_name", "Unknown")
    c.drawString(72, y, f"Name: {full_name}")
    y -= 14
    if metadata["user_type"] == "person_a":
        cibil = applicant.get("cibil_score", "N/A")
        loan_amt = applicant.get("loan_amount", "N/A")
        c.drawString(72, y, f"CIBIL Score: {cibil}")
        y -= 14
        c.drawString(72, y, f"Loan Amount: {loan_amt}")
        y -= 14
    else:
        biz = applicant.get("primary_business", "N/A")
        loan_amt = applicant.get("loan_amount", "N/A")
        c.drawString(72, y, f"Primary Business: {biz}")
        y -= 14
        c.drawString(72, y, f"Loan Amount: {loan_amt}")
        y -= 14

    # Verdict / readiness band
    y -= 14
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Verdict")
    y -= 18
    c.setFont("Helvetica", 10)
    if metadata["user_type"] == "person_a":
        eligibility = assessment.get("eligibility") or {}
        verdict = eligibility.get("verdict", "N/A")
        probability = eligibility.get("probability")
        c.drawString(72, y, f"Verdict: {verdict}")
        y -= 14
        if probability is not None:
            c.drawString(72, y, f"Probability: {probability:.4f}")
            y -= 14
    else:
        readiness = assessment.get("readiness") or {}
        score = readiness.get("score", "N/A")
        band = readiness.get("band", "N/A")
        c.drawString(72, y, f"Readiness Score: {score}")
        y -= 14
        c.drawString(72, y, f"Readiness Band:  {band}")
        y -= 14

    c.showPage()
    c.save()
    return buf.getvalue()


# ── Routes ────────────────────────────────────────────────────────────────


@router.post("/generate")
async def generate_report(request: Request):
    """Build a PDF report from a full assessment response body."""
    try:
        body = await request.json()
    except Exception:
        return _error(400, "VALIDATION_ERROR", "Request body is not valid JSON.")

    if not isinstance(body, dict):
        return _error(400, "VALIDATION_ERROR", "Request body must be a JSON object.")

    user_type = body.get("user_type")
    if user_type not in ("person_a", "person_b"):
        return _error(
            400,
            "INVALID_USER_TYPE",
            "user_type must be 'person_a' or 'person_b'.",
        )

    if "applicant" not in body:
        return _error(
            400,
            "MISSING_REQUIRED_FIELD",
            "Field 'applicant' is required in the assessment body.",
        )

    if user_type == "person_a" and "eligibility" not in body:
        return _error(
            400,
            "MISSING_REQUIRED_FIELD",
            "Field 'eligibility' is required for person_a reports.",
        )
    if user_type == "person_b" and "readiness" not in body:
        return _error(
            400,
            "MISSING_REQUIRED_FIELD",
            "Field 'readiness' is required for person_b reports.",
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_id = await run_in_threadpool(_build_report_id, user_type)
    metadata = {
        "report_id": report_id,
        "generated_at": timestamp,
        "user_type": user_type,
        "version": "1.0",
    }

    pdf_bytes = await run_in_threadpool(_render_pdf, body, metadata)
    await run_in_threadpool(
        _store_report,
        report_id,
        timestamp,
        user_type,
        "1.0",
        pdf_bytes,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="RiskIntel_Report_{report_id}.pdf"',
            "X-Report-Id": report_id,
        },
    )


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """Return the PDF for the given report_id (issued by /api/report/generate)."""
    if not _REPORT_ID_PATTERN.match(report_id):
        return _error(400, "VALIDATION_ERROR", "Malformed report_id.")

    pdf_bytes = await run_in_threadpool(_fetch_report_blob, report_id)
    if pdf_bytes is None:
        return _error(404, "REPORT_NOT_FOUND", f"No report found for id {report_id}.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="RiskIntel_Report_{report_id}.pdf"'},
    )
