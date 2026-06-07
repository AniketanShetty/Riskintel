"""
RiskTierResult model — E2 risk tier assignment output.

Stores the assigned tier (P1-P4) determined by the CIBIL-based
rule engine with reference to the exact rule version used.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskTierResult(Base):
    __tablename__ = "risk_tier_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(
        ForeignKey("rule_registry.id"), nullable=False,
    )
    assigned_tier: Mapped[str] = mapped_column(String(10), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(
        "Assessment", back_populates="risk_tier_result",
    )
    rule: Mapped["RuleRegistry"] = relationship("RuleRegistry")

    __table_args__ = (
        Index("idx_risk_tier_assessment", "assessment_id"),
    )

    def __repr__(self) -> str:
        return f"<RiskTierResult id={self.id} tier={self.assigned_tier}>"
