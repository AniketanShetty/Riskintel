"""
RuleRegistry model — versioned deterministic rule configurations for E1, E2, E5.

Each row captures the exact logic payload (thresholds, conditions) for
a specific engine at a specific version.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RuleRegistry(Base):
    __tablename__ = "rule_registry"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    engine_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    logic_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("engine_id", "version", name="uq_rule_engine_version"),
    )

    def __repr__(self) -> str:
        return f"<RuleRegistry id={self.id} engine={self.engine_id} v={self.version}>"
