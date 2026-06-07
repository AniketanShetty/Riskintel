"""Pydantic v2 schemas — request/response models for all API endpoints."""
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    HealthDependencyStatus,
)
from app.schemas.applicant import (
    ApplicantCreate,
    ApplicantResponse,
    ApplicantUpdate,
)
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentStatusEnum,
    AssessmentListResponse,
)

# Re-export for convenience
__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "HealthDependencyStatus",
    "ApplicantCreate",
    "ApplicantResponse",
    "ApplicantUpdate",
    "AssessmentCreate",
    "AssessmentResponse",
    "AssessmentStatusEnum",
    "AssessmentListResponse",
]
