"""
RecommendationResult model — predictive recommendation output (E4).

Stores the suggested credit limit and improvement actions.
Linked to the exact model version via model_id FK.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False,
    )
    model_id: Mapped[str] = mapped_column(
        ForeignKey("model_registry.id"), nullable=False,
    )
    suggested_limit: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    improvement_actions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(
        "Assessment", back_populates="recommendation_result",
    )
    model: Mapped[ModelRegistry] = relationship(
        "ModelRegistry", back_populates="recommendation_results",
    )

    __table_args__ = (
        Index("idx_recommendation_assessment", "assessment_id"),
    )

    def __repr__(self) -> str:
        return f"<RecommendationResult id={self.id} limit={self.suggested_limit}>"
