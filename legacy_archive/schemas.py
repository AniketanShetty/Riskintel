from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, UUID4, ConfigDict


class EducationLevel(str, Enum):
    OTHERS = "OTHERS"
    SSC = "SSC"
    TENTH = "10TH"
    TWELFTH = "12TH"
    UNDER_GRADUATE = "UNDER GRADUATE"
    GRADUATE = "GRADUATE"
    POST_GRADUATE = "POST-GRADUATE"
    PROFESSIONAL = "PROFESSIONAL"


class AssessmentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED_PROCESSING = "FAILED_PROCESSING"


class ApplicantCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "John"})
    last_name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "Doe"})
    email: EmailStr = Field(..., json_schema_extra={"example": "john.doe@example.com"})
    tax_id: str = Field(
        ..., 
        min_length=9, 
        max_length=20, 
        description="Plaintext SSN or PAN, will be hashed at the gateway.",
        json_schema_extra={"example": "ABCDE1234F"}
    )


class FinancialFeatures(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    cibil_score: int = Field(..., ge=300, le=900, json_schema_extra={"example": 750})
    net_monthly_income: float = Field(..., gt=0, json_schema_extra={"example": 85000.50})
    age: int = Field(..., ge=18, le=100, json_schema_extra={"example": 35})
    time_with_curr_empr: int = Field(..., ge=0, json_schema_extra={"example": 48})
    education: EducationLevel = Field(..., json_schema_extra={"example": "GRADUATE"})


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applicant: ApplicantCreate
    financial_features: FinancialFeatures


class DecisionSummary(BaseModel):
    eligibility: str = Field(..., json_schema_extra={"example": "PASS"})
    risk_tier: Optional[str] = Field(None, json_schema_extra={"example": "P2"})
    archetype: Optional[str] = Field(None, json_schema_extra={"example": "Mid-Career Established"})
    credit_limit: Optional[float] = Field(None, json_schema_extra={"example": 125000.00})
    readiness: Optional[str] = Field(None, json_schema_extra={"example": "READY"})


class LineageMetadata(BaseModel):
    e1_rule_version: str = Field(..., json_schema_extra={"example": "v1.0.2"})
    e2_rule_version: Optional[str] = Field(None, json_schema_extra={"example": "v1.1.0"})
    e3_model_id: Optional[str] = Field(None, json_schema_extra={"example": "m-883a-kmns-v2.1"})
    e4_model_id: Optional[str] = Field(None, json_schema_extra={"example": "m-994b-recs-v1.8"})
    e5_rule_version: Optional[str] = Field(None, json_schema_extra={"example": "v1.0.0"})


class AuditMetadata(BaseModel):
    correlation_id: UUID4
    execution_time_ms: int = Field(..., ge=0)


class AssessmentResponse(BaseModel):
    assessment_id: UUID4
    status: AssessmentStatus
    rejection_reason: Optional[str] = Field(None, json_schema_extra={"example": "Applicant credit score is below threshold."})
    decision_summary: DecisionSummary
    improvement_actions: Optional[List[str]] = Field(None, json_schema_extra={"example": ["Decrease current credit utilization."]})
    audit_metadata: AuditMetadata
    lineage_metadata: LineageMetadata


class ArchetypeResponse(BaseModel):
    model_id: UUID4
    archetype_label: str = Field(..., json_schema_extra={"example": "High-Income Established"})
    cluster_distances: Optional[Dict[str, float]] = Field(None, json_schema_extra={"example": {"cluster_0": 2.5, "cluster_1": 0.4}})


class RecommendationResponse(BaseModel):
    model_id: UUID4
    suggested_limit: float = Field(..., gt=0, json_schema_extra={"example": 150000.00})
    improvement_actions: Optional[List[str]] = Field(None, json_schema_extra={"example": ["Increase age of oldest active tradeline."]})


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correlation_id: UUID4
    assessment_id: UUID4
    engine_id: str = Field(..., min_length=2, max_length=50, json_schema_extra={"example": "E3"})
    event_type: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "E3_INFERENCE_SUCCESS"})
    payload: Optional[Dict[str, Any]] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)
