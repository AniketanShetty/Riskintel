"""
Applicant Pydantic schemas for create, read, and update operations.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ApplicantCreate(BaseModel):
    """Request schema for creating a new applicant."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str = Field(
        ..., min_length=1, max_length=100,
        json_schema_extra={"example": "John"},
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100,
        json_schema_extra={"example": "Doe"},
    )
    email: EmailStr = Field(
        ..., json_schema_extra={"example": "john.doe@example.com"},
    )
    tax_id: str = Field(
        ..., min_length=9, max_length=20,
        description="Plaintext SSN or PAN; will be hashed at the gateway.",
        json_schema_extra={"example": "ABCDE1234F"},
    )


class ApplicantUpdate(BaseModel):
    """Request schema for updating an existing applicant (partial)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: Optional[str] = Field(
        None, min_length=1, max_length=100,
    )
    last_name: Optional[str] = Field(
        None, min_length=1, max_length=100,
    )
    email: Optional[EmailStr] = None


class ApplicantResponse(BaseModel):
    """Response schema for applicant data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    updated_at: datetime
