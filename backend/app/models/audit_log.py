"""
AuditLog model — immutable, append-only ledger for the Orchestrator DAG.

An UPDATE trigger prevents any modification after insertion.
See docs/schema_explanation.md for compliance rationale.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False,
    )
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    engine_id: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(
        "Assessment", back_populates="audit_logs",
    )

    __table_args__ = (
        Index("idx_audit_assessment_id", "assessment_id"),
        Index("idx_audit_correlation_id", "correlation_id"),
        Index("idx_audit_logged_at", "logged_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} event={self.event_type}>"
