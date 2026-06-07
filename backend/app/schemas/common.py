"""
Common Pydantic schemas shared across the API.

Includes:
- Standardised error response shapes
- Health check response models
- Pagination metadata
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Error Responses (matches docs/output_contracts.md §5) ─────────────────


class ErrorDetail(BaseModel):
    """Per-field validation error detail."""

    field: str = Field(..., description="Internal field name that failed")
    value: Any = Field(..., description="The value that was submitted")
    rule: str = Field(..., description="The validation rule that was violated")
    message: str = Field(..., description="Human-readable explanation")


class ErrorBody(BaseModel):
    """Machine-readable error payload."""

    code: str = Field(..., description="Error code, e.g. VALIDATION_ERROR")
    message: str = Field(..., description="Human-readable summary")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Per-field errors, present only for VALIDATION_ERROR",
    )


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    status: str = Field("error", description="Always 'error'")
    error: ErrorBody


# ── Health Check Responses ────────────────────────────────────────────────


class HealthDependencyStatus(BaseModel):
    """Status of a single external dependency."""

    status: str = Field(..., description="One of: CONNECTED, DISCONNECTED, ERROR")
    detail: Optional[str] = Field(None, description="Optional detail message")


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = Field(..., description="UP, DOWN, or DEGRADED")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Optional[Dict[str, str]] = Field(
        None, description="Dependency status map (ready endpoint)",
    )
