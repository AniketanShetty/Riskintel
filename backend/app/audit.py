"""
audit.py

Handles transaction auditing with SQLite. Ensures fail-closed behavior for all decisions.
"""
import os
import sqlite3
import json
from typing import Dict, Any
from app.exceptions import AuditLogError
from app.core.config import settings

def get_db_path() -> str:
    """Returns the absolute path to the centralized SQLite database."""
    return str(settings.DB_PATH_ABS)

def init_db() -> None:
    """Initialize SQLite database and ensure audit_log + reports tables exist."""
    path = get_db_path()
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                correlation_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                api_version TEXT NOT NULL,
                request_schema_version TEXT NOT NULL,
                decision_version TEXT NOT NULL,
                recommendation_version TEXT NOT NULL,
                model_lineage_bind TEXT NOT NULL,
                final_verdict TEXT NOT NULL,
                engine_statuses TEXT NOT NULL,
                triggered_rule_ids TEXT NOT NULL,
                policy_override_flags TEXT NOT NULL,
                request_payload_hash TEXT,
                user_type_original TEXT,
                routing_decision TEXT
            );
        """)
        # Reports table — same DB so reports survive process restarts.
        # report_id is the canonical primary key (e.g. RI-20260606-A-00001).
        # pdf_blob holds the raw PDF bytes generated for that id.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                generated_at TEXT NOT NULL,
                user_type TEXT NOT NULL,
                version TEXT NOT NULL,
                pdf_blob BLOB NOT NULL
            );
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reports_user_type_generated_at "
            "ON reports (user_type, generated_at);"
        )
        # Health check table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_check (
                id INTEGER PRIMARY KEY,
                val TEXT NOT NULL
            );
        """)

        # Forward-only schema migration for audit_log (additive columns).
        # SQLite has no ALTER TABLE … ADD COLUMN IF NOT EXISTS, so probe
        # pragma_table_info and add only what is missing. Safe for both
        # fresh and pre-existing databases.
        cursor.execute("PRAGMA table_info(audit_log);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        audit_log_additions = {
            "request_payload_hash": "TEXT",
            "user_type_original": "TEXT",
            "routing_decision": "TEXT",
            "serialized_response_json": "TEXT",
        }
        for col, ddl_type in audit_log_additions.items():
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE audit_log ADD COLUMN {col} {ddl_type};")

        conn.commit()
    except sqlite3.Error as e:
        raise AuditLogError(f"Failed to initialize database: {e}")
    finally:
        if conn:
            conn.close()

def write_audit_record(record: Dict[str, Any]) -> None:
    """
    Writes audit transaction record to the SQLite database.
    Guarantees strict fail-closed policy: must succeed or raises AuditLogError.
    """
    init_db()  # Ensure tables exist
    path = get_db_path()
    
    conn = None
    try:
        conn = sqlite3.connect(path, timeout=5.0)  # Add timeout for busy DBs
        cursor = conn.cursor()
        
        # Serialize dictionaries and lists to JSON strings
        model_lineage_bind = json.dumps(record.get("model_lineage_bind", {}))
        engine_statuses = json.dumps(record.get("engine_statuses", {}))
        triggered_rule_ids = json.dumps(record.get("triggered_rule_ids", []))
        policy_override_flags = json.dumps(record.get("policy_override_flags", []))
        routing_decision = json.dumps(record.get("routing_decision", {}))

        cursor.execute(
            """
            INSERT INTO audit_log (
                correlation_id, timestamp, api_version, request_schema_version,
                decision_version, recommendation_version, model_lineage_bind,
                final_verdict, engine_statuses, triggered_rule_ids, policy_override_flags,
                request_payload_hash, user_type_original, routing_decision,
                serialized_response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("correlation_id"),
                record.get("timestamp"),
                record.get("api_version", "v1"),
                record.get("request_schema_version", "1.0"),
                record.get("decision_version", "1.2"),
                record.get("recommendation_version", "1.1"),
                model_lineage_bind,
                record.get("final_verdict"),
                engine_statuses,
                triggered_rule_ids,
                policy_override_flags,
                record.get("request_payload_hash"),
                record.get("user_type_original"),
                routing_decision,
                record.get("serialized_response_json"),
            )
        )
        conn.commit()
    except sqlite3.Error as e:
        # Strict Fail-Closed Policy: convert database errors into AuditLogError
        raise AuditLogError(f"Database write failed during audit log commit: {e}")
    finally:
        if conn:
            conn.close()

def check_db_write_capability() -> bool:
    """
    Validates SQLite write capability. Used for Deep Health check.
    Attempts to write and roll back or delete a temporary row.
    """
    init_db()
    path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(path, timeout=2.0)
        cursor = conn.cursor()
        # Insert and delete a row to test write capability safely
        cursor.execute("INSERT INTO health_check (val) VALUES ('test')")
        cursor.execute("DELETE FROM health_check WHERE val = 'test'")
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        if conn:
            conn.close()
