from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.enums import BureauGateStatus, VerificationStatus, LoanTerm, LoanPurpose, IncomeBracket, ArtifactType
import enum

class IntakeRequest(BaseModel):
    loan_amount: int = Field(..., ge=1000, le=500000)
    loan_term: LoanTerm
    loan_purpose: LoanPurpose
    income_bracket: IncomeBracket
    full_name: str = Field(...)
    national_id: str = Field(...)
    pincode: str = Field(...)

class TriageRequest(BaseModel):
    bureau_status: BureauGateStatus

class AAWebhookStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

class AAVerificationWebhook(BaseModel):
    session_id: str
    status: AAWebhookStatus
    verified_income: Optional[int] = None

class FOVerificationWebhook(BaseModel):
    session_id: str
    status: VerificationStatus
    verified_income: Optional[int] = None

class VerificationWebhook(BaseModel):
    session_id: str
    status: VerificationStatus
    verified_income: Optional[int] = None

class RepromptRequest(BaseModel):
    secondary_contact: str

class CoApplicantRequest(BaseModel):
    full_name: str = Field(...)
    national_id: str = Field(...)
    pincode: str = Field(...)

class ArtifactUploadRequest(BaseModel):
    artifact_type: ArtifactType
    file_hash: str

class OptimizationRequest(BaseModel):
    annual_rate: float = Field(default=0.18, ge=0.01, le=1.0)

class SessionResponse(BaseModel):
    session_id: str
    current_state: str
    
    class Config:
        from_attributes = True

class ApplicationListResponse(BaseModel):
    id: str
    current_state: str
    loan_amount: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaginatedApplicationList(BaseModel):
    items: List[ApplicationListResponse]
    total: int
    limit: int
    skip: int

class ApprovedTerms(BaseModel):
    final_loan_amount: int
    final_tenure_months: int
    monthly_emi: int
    next_steps: str

class CounterOffer(BaseModel):
    reason: str
    proposed_loan_amount: int
    proposed_tenure_months: int
    proposed_monthly_emi: int

class RejectionDetails(BaseModel):
    reason: str
    actionable_advice: str

class RepromptRequirements(BaseModel):
    missing_fields: List[str]
    instructions: str

class DecisionExplanation(BaseModel):
    approved_terms: Optional[ApprovedTerms] = None
    counter_offer: Optional[CounterOffer] = None
    rejection_details: Optional[RejectionDetails] = None
    reprompt_requirements: Optional[RepromptRequirements] = None

class ApplicationDetailResponse(BaseModel):
    id: str
    current_state: str
    loan_amount: int
    loan_term: LoanTerm
    loan_purpose: LoanPurpose
    income_bracket: IncomeBracket
    bureau_gate_status: Optional[BureauGateStatus] = None
    triage_pass: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    explanation: Optional[DecisionExplanation] = None

    class Config:
        from_attributes = True

class DeadLetterResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    route: str
    raw_payload: str
    failure_reason: str
    error_details: Optional[str] = None
    occurred_at: datetime

    class Config:
        from_attributes = True

class PaginatedDeadLetterList(BaseModel):
    items: List[DeadLetterResponse]
    total: int
    limit: int
    skip: int
