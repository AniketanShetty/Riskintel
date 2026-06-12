import uuid
from sqlalchemy import String, Boolean, ForeignKey, Float, Integer, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

class ApplicantProfile(Base):
    """
    Stores both primary and co-applicant profiles in a single table.
    is_co_applicant flag discriminates between them.
    Nullable co-applicant fields are enforced at the application layer.
    """
    __tablename__ = "applicant_profiles"

    __table_args__ = (
        CheckConstraint(
            "is_co_applicant = TRUE OR (full_name IS NOT NULL AND national_id IS NOT NULL AND pincode IS NOT NULL)",
            name="chk_primary_applicant_required_fields"
        ),
        UniqueConstraint("session_id", "is_co_applicant", name="uq_session_applicant_type"),
        Index("ix_applicants_session", "session_id")
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    is_co_applicant: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Intake data
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    national_id: Mapped[str] = mapped_column(String(12), nullable=False)    # PAN (10) or Aadhaar (12)
    pincode: Mapped[str] = mapped_column(String(6), nullable=False)

    # Canonical normalization outputs (ADR-022)
    canonical_verified_income: Mapped[int | None] = mapped_column(Integer, nullable=True)
    canonical_vintage_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    canonical_verification_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Co-applicant specific (ADR-025)
    co_app_canonical_verification_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    co_app_pathway: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Bureau data (Person A only)
    cibil_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    national_id_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Unidirectional relationship to parent
    session: Mapped["ApplicationSession"] = relationship(
        "ApplicationSession", 
        foreign_keys=[session_id],
        overlaps="primary_applicant,co_applicant"
    )
