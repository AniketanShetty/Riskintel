"""
Applicant model — core identity and PII storage.

Tax ID is stored as a salted SHA-256 hash for security.
See docs/schema_explanation.md for compliance rationale.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class Applicant(Base):
    __tablename__ = "applicants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tax_id_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    assessments: Mapped[List[Assessment]] = relationship(
        "Assessment", back_populates="applicant", cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_applicants_email", "email"),
        Index("idx_applicants_tax_id_hash", "tax_id_hash"),
    )

    def __repr__(self) -> str:
        return f"<Applicant id={self.id} email={self.email}>"
