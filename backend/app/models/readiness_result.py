"""
ReadinessResult model — E5 readiness assessment output.

Stores the binary readiness decision and any blocking conditions
determined by the rule-based E5 engine for Person B workflows.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReadinessResult(Base):
    __tablename__ = "readiness_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(
        ForeignKey("rule_registry.id"), nullable=False,
    )
    is_ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    blocking_conditions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(
        "Assessment", back_populates="readiness_result",
    )
    rule: Mapped["RuleRegistry"] = relationship("RuleRegistry")

    __table_args__ = (
        Index("idx_readiness_assessment", "assessment_id"),
    )

    def __repr__(self) -> str:
        return f"<ReadinessResult id={self.id} ready={self.is_ready}>"
