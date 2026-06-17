from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from db.base import Base

class DeadLetterWebhook(Base):
    __tablename__ = "dead_letter_webhooks"

    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    route = Column(String(255), nullable=False)
    raw_payload = Column(Text, nullable=False)
    failure_reason = Column(String(255), nullable=False)
    error_details = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
