import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, CheckConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from models.enums import ApplicationState, LoanPurpose, LoanTerm, IncomeBracket, BureauGateStatus
from models.applicant import ApplicantProfile

class ApplicationSession(Base):
    """
    Root record. One row per loan application lifecycle.
    Owns the state machine cursor.
    """
    __tablename__ = "application_sessions"

    __table_args__ = (
        CheckConstraint("loan_amount >= 1000 AND loan_amount <= 500000", name="chk_loan_amount_bounds"),
        CheckConstraint("loan_term IN (12, 18, 24, 36, 48, 60)", name="chk_loan_term_valid"),
        CheckConstraint("current_state IN ('INTAKE', 'TRIAGE', 'PENDING_VERIFICATION', 'PENDING_REPROMPT', 'VERIFIED', 'OPTIMIZATION', 'READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_application_state_enum"),
        CheckConstraint("loan_purpose IN ('medical', 'working_capital', 'education', 'home_repair', 'debt_consolidation', 'wedding', 'two_wheeler')", name="chk_loan_purpose_enum"),
        CheckConstraint("income_bracket IN ('0-10k', '10k-20k', '20k-30k', '30k-40k', '40k-50k', '50k+')", name="chk_income_bracket_enum"),
        CheckConstraint("bureau_gate_status IS NULL OR bureau_gate_status IN ('PRIME', 'SUB_PRIME', 'THIN_FILE')", name="chk_bureau_gate_status_enum"),
        Index("ix_sessions_state", "current_state")
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    current_state: Mapped[ApplicationState] = mapped_column(String(30), nullable=False, server_default="INTAKE")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Loan request fields (immutable after INTAKE submission)
    loan_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    loan_term: Mapped[LoanTerm] = mapped_column(Integer, nullable=False)
    loan_purpose: Mapped[LoanPurpose] = mapped_column(String(30), nullable=False)
    income_bracket: Mapped[IncomeBracket] = mapped_column(String(15), nullable=False)

    # Bureau gate result (set during TRIAGE)
    bureau_gate_status: Mapped[BureauGateStatus | None] = mapped_column(String(15), nullable=True)
    triage_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


    # Relationships (Using unidirectional explicit mapping to prevent Identity Map corruption)
    primary_applicant: Mapped["ApplicantProfile"] = relationship(
        "ApplicantProfile",
        primaryjoin="and_(ApplicantProfile.session_id == ApplicationSession.id, "
                    "ApplicantProfile.is_co_applicant == False)",
        uselist=False, 
        overlaps="session,co_applicant",
        cascade="all, delete-orphan"
    )
    co_applicant: Mapped["ApplicantProfile | None"] = relationship(
        "ApplicantProfile",
        primaryjoin="and_(ApplicantProfile.session_id == ApplicationSession.id, "
                    "ApplicantProfile.is_co_applicant == True)",
        uselist=False,
        overlaps="session,primary_applicant",
        cascade="all, delete-orphan"
    )
    verifications: Mapped[list["VerificationRecord"]] = relationship(
        "VerificationRecord", back_populates="session"
    )
    state_events: Mapped[list["StateTransitionEvent"]] = relationship(
        "StateTransitionEvent", back_populates="session", order_by="StateTransitionEvent.occurred_at"
    )
    optimization_results: Mapped[list["OptimizationResult"]] = relationship(
        "OptimizationResult", back_populates="session",
        order_by="OptimizationResult.attempt_number"
    )

    @property
    def aa_retry_count(self) -> int:
        return sum(1 for e in self.state_events if e.trigger_event in ('AA_PULL_FAILED_RETRY', 'AA_PULL_EXHAUSTED_FALLBACK'))

    @property
    def fo_retry_count(self) -> int:
        return sum(1 for e in self.state_events if e.trigger_event in ('FO_UNREACHABLE_RETRY', 'FO_UNREACHABLE_MAX_RETRIES', 'MISSING_SECONDARY_CONTACT', 'USER_REFUSAL'))
