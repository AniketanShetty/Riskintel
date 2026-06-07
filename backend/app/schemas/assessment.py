"""
Assessment Pydantic schemas for initiating and retrieving assessments.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class AssessmentStatusEnum(str, Enum):
    """Valid assessment lifecycle states."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED_PROCESSING = "FAILED_PROCESSING"


class AssessmentCreate(BaseModel):
    """Request schema to trigger a new assessment pipeline run."""

    model_config = ConfigDict(extra="forbid")

    applicant_id: uuid.UUID = Field(
        ..., description="UUID of the existing applicant record",
    )
    input_features: Dict[str, Any] = Field(
        ..., description="Raw feature vector snapshot",
    )


class AssessmentResponse(BaseModel):
    """Response schema for a single assessment record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_id: uuid.UUID
    status: AssessmentStatusEnum
    input_features: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None


class AssessmentListResponse(BaseModel):
    """Paginated list of assessments."""

    items: List[AssessmentResponse]
    total: int
    page: int
    page_size: int
