import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, CheckConstraint, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from models.enums import VerificationSource, VerificationStatus, ArtifactType

class VerificationRecord(Base):
    """
    One record per verification attempt. Multiple are possible within PENDING_VERIFICATION.
    Tamper evidence hashes are stored immutably.
    """
    __tablename__ = "verification_records"

    __table_args__ = (
        CheckConstraint("business_vintage_months_derived IS NULL OR business_vintage_months_derived >= 0", name="chk_vintage_months_nonnegative"),
        CheckConstraint("verified_monthly_cash_income IS NULL OR verified_monthly_cash_income >= 0", name="chk_verified_income_nonnegative"),
        CheckConstraint("verification_source IN ('FIELD_OFFICER', 'ACCOUNT_AGGREGATOR')", name="chk_verification_source_enum"),
        CheckConstraint("verification_status IN ('VERIFIED_CLEAN', 'VERIFIED_WITH_VARIANCE', 'FRAUD_DETECTED', 'UNREACHABLE', 'MISSING_SECONDARY_CONTACT')", name="chk_verification_status_enum"),
        CheckConstraint("artifact_type IS NULL OR artifact_type IN ('municipal_license', 'rent_agreement', 'merchant_qr', 'none')", name="chk_artifact_type_enum"),
        UniqueConstraint("session_id", "attempt_number", name="uq_verification_attempt"),
        Index("ix_verifications_session", "session_id")
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Source and status
    verification_source: Mapped[VerificationSource] = mapped_column(String(25), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(String(30), nullable=False)

    # Verified financial data
    verified_monthly_cash_income: Mapped[int | None] = mapped_column(Integer, nullable=True)
    secondary_contact_number: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # Tamper evidence
    fo_visit_photo_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tamper_evidence_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Vintage artifact
    artifact_type: Mapped[ArtifactType | None] = mapped_column(String(25), nullable=True)
    artifact_issue_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    artifact_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    business_vintage_months_derived: Mapped[int | None] = mapped_column(Integer, nullable=True)

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="verifications")


class OptimizationResult(Base):
    """
    One row per optimization attempt. Multiple rows are permitted per session
    to support the co-applicant recovery flow (NEARLY_READY -> VERIFIED -> OPTIMIZATION).
    Each row is immutable after creation. Attempt ordering is preserved via attempt_number.
    """
    __tablename__ = "optimization_results"

    __table_args__ = (
        CheckConstraint("approved_loan_amount >= 1000 AND approved_loan_amount <= 500000", name="chk_approved_amount_bounds"),
        CheckConstraint("approved_tenure >= 12 AND approved_tenure <= 60", name="chk_approved_tenure_bounds"),
        CheckConstraint("repayment_trust IN ('PASS', 'FAIL')", name="chk_repayment_trust_enum"),
        CheckConstraint("decision_verdict IN ('READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_decision_verdict_enum"),
        UniqueConstraint("session_id", "attempt_number", name="uq_optimization_attempt")
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Scorecard metrics
    repayment_trust: Mapped[str] = mapped_column(String(4), nullable=False)
    available_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    target_emi: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    contract_emi: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Optimization outputs
    approved_loan_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_tenure: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coapplicant_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    required_coapplicant_income_baseline: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Decision explanation
    decision_verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    primary_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    recovery_roadmap: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    livelihood_resilience_pass: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="optimization_results")

    @property
    def emi_shortfall(self) -> int:
        return max(0, self.target_emi - self.available_capacity)
