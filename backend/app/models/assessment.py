"""
Assessment model — represents a single run of the RiskIntel pipeline.

Captures the exact input feature vector at application time (immutable snapshot).
Status transitions: PENDING -> APPROVED | REJECTED | FAILED_PROCESSING
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.applicant import Applicant
    from app.models.archetype_result import ArchetypeResult
    from app.models.audit_log import AuditLog
    from app.models.eligibility_result import EligibilityResult
    from app.models.readiness_result import ReadinessResult
    from app.models.recommendation_result import RecommendationResult
    from app.models.risk_tier_result import RiskTierResult


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    applicant_id: Mapped[str] = mapped_column(
        ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False,
    )
    input_features: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    applicant: Mapped[Applicant] = relationship(
        "Applicant", back_populates="assessments",
    )
    eligibility_result: Mapped[Optional[EligibilityResult]] = relationship(
        "EligibilityResult", back_populates="assessment", uselist=False,
        cascade="all, delete-orphan",
    )
    risk_tier_result: Mapped[Optional[RiskTierResult]] = relationship(
        "RiskTierResult", back_populates="assessment", uselist=False,
        cascade="all, delete-orphan",
    )
    archetype_result: Mapped[Optional[ArchetypeResult]] = relationship(
        "ArchetypeResult", back_populates="assessment", uselist=False,
        cascade="all, delete-orphan",
    )
    recommendation_result: Mapped[Optional[RecommendationResult]] = relationship(
        "RecommendationResult", back_populates="assessment", uselist=False,
        cascade="all, delete-orphan",
    )
    readiness_result: Mapped[Optional[ReadinessResult]] = relationship(
        "ReadinessResult", back_populates="assessment", uselist=False,
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List[AuditLog]] = relationship(
        "AuditLog", back_populates="assessment", cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'FAILED_PROCESSING')",
            name="chk_status",
        ),
        Index("idx_assessments_applicant_id", "applicant_id"),
    )

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} status={self.status}>"
