import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from models.enums import ApplicationState

class StateTransitionEvent(Base):
    """
    Immutable append-only audit ledger.
    Every state transition writes one row.
    Never updated, never deleted.
    """
    __tablename__ = "state_transition_events"

    __table_args__ = (
        CheckConstraint("from_state IN ('INTAKE', 'TRIAGE', 'PENDING_VERIFICATION', 'PENDING_REPROMPT', 'VERIFIED', 'OPTIMIZATION', 'READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_from_state_enum"),
        CheckConstraint("to_state IN ('INTAKE', 'TRIAGE', 'PENDING_VERIFICATION', 'PENDING_REPROMPT', 'VERIFIED', 'OPTIMIZATION', 'READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_to_state_enum"),
        Index("ix_events_session_time", "session_id", "occurred_at")
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    from_state: Mapped[ApplicationState] = mapped_column(String(30), nullable=False)
    to_state: Mapped[ApplicationState] = mapped_column(String(30), nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    actor: Mapped[str] = mapped_column(String(100), nullable=False)

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="state_events")
