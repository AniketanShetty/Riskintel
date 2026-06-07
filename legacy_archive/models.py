import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Applicant(Base):
    __tablename__ = "applicants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tax_id_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="applicant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_applicants_email", "email"),
        Index("idx_applicants_tax_id_hash", "tax_id_hash"),
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    input_features: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    applicant: Mapped["Applicant"] = relationship("Applicant", back_populates="assessments")
    archetype_result: Mapped[Optional["ArchetypeResult"]] = relationship("ArchetypeResult", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    recommendation_result: Mapped[Optional["RecommendationResult"]] = relationship("RecommendationResult", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="assessment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(status.in_(["PENDING", "APPROVED", "REJECTED", "FAILED_PROCESSING"]), name="chk_status"),
        Index("idx_assessments_applicant_id", "applicant_id"),
        Index("idx_assessments_features_gin", "input_features", postgresql_using="gin"),
    )


class RuleRegistry(Base):
    __tablename__ = "rule_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engine_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    logic_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_active_rules", "engine_id", postgresql_where=text("is_active = TRUE")),
    )


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engine_id: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    artifact_s3_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    training_data_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    archetype_results: Mapped[List["ArchetypeResult"]] = relationship("ArchetypeResult", back_populates="model")
    recommendation_results: Mapped[List["RecommendationResult"]] = relationship("RecommendationResult", back_populates="model")

    __table_args__ = (
        Index("idx_active_models", "engine_id", postgresql_where=text("is_active = TRUE")),
    )


class ArchetypeResult(Base):
    __tablename__ = "archetype_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_registry.id"), nullable=False)
    archetype_label: Mapped[str] = mapped_column(String(100), nullable=False)
    cluster_distances: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="archetype_result")
    model: Mapped["ModelRegistry"] = relationship("ModelRegistry", back_populates="archetype_results")

    __table_args__ = (
        Index("idx_archetype_assessment", "assessment_id"),
    )


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_registry.id"), nullable=False)
    suggested_limit: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    improvement_actions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="recommendation_result")
    model: Mapped["ModelRegistry"] = relationship("ModelRegistry", back_populates="recommendation_results")

    __table_args__ = (
        Index("idx_recommendation_assessment", "assessment_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    engine_id: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_assessment_id", "assessment_id"),
        Index("idx_audit_correlation_id", "correlation_id"),
        Index("idx_audit_logged_at", "logged_at"),
    )
