"""
Pytest configuration and shared fixtures for the RiskIntel test suite.

Goals:
  - Test isolation: each suite that touches the unified SQLite database
    starts and ends from a clean state.
  - No dual database paths: all persistence assertions go through the
    single audit module path (settings.DB_PATH_ABS). Reports are persisted
    in the same DB (table `reports`).
  - Shared fixtures for the DB path, audit row count, and reports row count.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.audit import get_db_path, init_db
from app.core.config import settings


# ── Session-wide safety net ────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def _ensure_db_schema_session():
    """Make sure both `audit_log` and `reports` tables exist before any test."""
    init_db()
    yield


# ── Module-level isolation for persistence tests ───────────────────────────


@pytest.fixture
def db_path():
    """Path to the unified SQLite DB (the only DB in the system)."""
    return Path(get_db_path())


@pytest.fixture
def audit_row_count(db_path):
    """Current audit_log row count as int. 0 if table not present."""
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log';"
        )
        if cur.fetchone() is None:
            return 0
        cur.execute("SELECT COUNT(*) FROM audit_log;")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


@pytest.fixture
def reports_row_count(db_path):
    """Current reports row count as int. 0 if table not present."""
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='reports';"
        )
        if cur.fetchone() is None:
            return 0
        cur.execute("SELECT COUNT(*) FROM reports;")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


@pytest.fixture
def clean_reports(db_path, reports_row_count):
    """Snapshot reports row count, truncate after the test, return the before-count."""
    before = reports_row_count
    yield before
    # Cleanup: delete any report rows added during the test.
    if db_path.exists():
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        try:
            conn.execute("DELETE FROM reports;")
            conn.commit()
        finally:
            conn.close()


@pytest.fixture(autouse=True)
def _truncate_reports_table_per_test(db_path):
    """Auto-truncate the `reports` table before each test.

    The reports table is durable across runs; without this fixture, two
    sequential test runs collide on PRIMARY KEY. Tests that don't touch
    the reports table still pay the trivial cost of one DELETE.
    """
    if db_path.exists():
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        try:
            conn.execute("DELETE FROM reports;")
            conn.commit()
        finally:
            conn.close()
    yield
