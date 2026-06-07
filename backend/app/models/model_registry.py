"""
ModelRegistry model — versioned ML artifact tracking for E3 and E4.

Each row captures the S3 URI and training data hash, enabling
full reproducibility and audit traceability.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.archetype_result import ArchetypeResult
    from app.models.recommendation_result import RecommendationResult


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    engine_id: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    artifact_s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    training_data_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    archetype_results: Mapped[List[ArchetypeResult]] = relationship(
        "ArchetypeResult", back_populates="model",
    )
    recommendation_results: Mapped[List[RecommendationResult]] = relationship(
        "RecommendationResult", back_populates="model",
    )

    __table_args__ = (
        UniqueConstraint("engine_id", "model_version", name="uq_model_engine_version"),
    )

    def __repr__(self) -> str:
        return f"<ModelRegistry id={self.id} engine={self.engine_id} v={self.model_version}>"
