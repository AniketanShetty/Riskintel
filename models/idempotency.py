import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class IdempotencyRecord(Base):
    """
    Deduplication ledger for idempotent API requests.

    Keyed on (idempotency_key, route). The first request for a given key
    is processed and the response is stored here. Subsequent requests
    with the same key return the cached response without re-executing.

    Rows are never updated after creation. They expire based on
    application policy (not enforced at the DB level — handled by the
    dependency layer).
    """
    __tablename__ = "idempotency_records"

    __table_args__ = (
        UniqueConstraint("idempotency_key", "route", name="uq_idempotency_key_route"),
        Index("ix_idempotency_key", "idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    route: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_body: Mapped[str] = mapped_column(Text, nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
