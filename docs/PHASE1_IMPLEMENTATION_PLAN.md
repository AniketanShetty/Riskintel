# RiskIntel V2 — Phase 1 Implementation Plan
## Database Schema, Core Models, and Migrations

---

## 1. Repository Structure

```
riskintel_v2/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_v2_init.py
├── config/
│   └── constants.py
├── db/
│   └── base.py
├── models/
│   ├── __init__.py
│   ├── enums.py
│   ├── session.py
│   ├── applicant.py
│   ├── verification.py
│   └── state_event.py
├── schemas/
│   ├── __init__.py
│   └── enums.py
├── registries/
│   ├── divisibility_registry.py
│   └── pincode_tier_mapping_v1.csv
└── tests/
    └── phase1/
        ├── test_models.py
        ├── test_enums.py
        └── test_migrations.py
```

---

## 2. System Constants

**`config/constants.py`**
```python
from decimal import Decimal

# ADR-024 — Deterministic System Constants
SYSTEM_BASE_INTEREST_RATE: Decimal = Decimal("0.24")   # 24% APR fixed
SYSTEM_MAX_TENURE: int = 60                             # months
SYSTEM_MIN_LOAN_AMOUNT: int = 1_000                    # INR
SYSTEM_MAX_LOAN_AMOUNT: int = 500_000                  # INR (5 Lakhs)
SYSTEM_BASE_SUBSISTENCE_LINE: int = 2_500              # INR/month
MAX_DTI: Decimal = Decimal("0.50")                     # 50% Debt-to-Income cap
CIBIL_PRIME_THRESHOLD: int = 650
BUREAU_MIN_VINTAGE_MONTHS: int = 12
PINCODE_DEFAULT_TIER: int = 1                          # Fallback per ADR-024 §5
PINCODE_TIER_MULTIPLIERS: dict[int, Decimal] = {
    1: Decimal("1.8"),
    2: Decimal("1.4"),
    3: Decimal("1.0"),
}
VERIFICATION_MAX_RETRY_DAYS: int = 14
VERIFICATION_MAX_RETRY_ATTEMPTS: int = 2
```

---

## 3. Enum Definitions

**`models/enums.py`**
```python
import enum

# --- Application State Machine ---
class ApplicationState(str, enum.Enum):
    INTAKE              = "INTAKE"
    TRIAGE              = "TRIAGE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_REPROMPT    = "PENDING_REPROMPT"      # ADR-025
    VERIFIED            = "VERIFIED"
    OPTIMIZATION        = "OPTIMIZATION"
    READY               = "READY"
    NEARLY_READY        = "NEARLY_READY"
    NOT_READY_YET       = "NOT_READY_YET"

# --- ADR-024 §3.1 — Income Bracket ---
class IncomeBracket(str, enum.Enum):
    ZERO_TO_10K  = "0-10k"
    TEN_TO_20K   = "10k-20k"
    TWENTY_TO_30K= "20k-30k"
    THIRTY_TO_40K= "30k-40k"
    FORTY_TO_50K = "40k-50k"
    ABOVE_50K    = "50k+"

# --- ADR-024 §3.2 — Loan Term ---
class LoanTerm(int, enum.Enum):
    MONTHS_12 = 12
    MONTHS_18 = 18
    MONTHS_24 = 24
    MONTHS_36 = 36
    MONTHS_48 = 48
    MONTHS_60 = 60

# --- ADR-024 §3.3 — Loan Purpose ---
class LoanPurpose(str, enum.Enum):
    MEDICAL             = "medical"
    WORKING_CAPITAL     = "working_capital"
    EDUCATION           = "education"
    HOME_REPAIR         = "home_repair"
    DEBT_CONSOLIDATION  = "debt_consolidation"
    WEDDING             = "wedding"
    TWO_WHEELER         = "two_wheeler"

# --- ADR-024 §4 — Divisibility Class ---
class DivisibilityClass(str, enum.Enum):
    DIVISIBLE   = "DIVISIBLE"
    INDIVISIBLE = "INDIVISIBLE"

# --- Bureau Gate Status ---
class BureauGateStatus(str, enum.Enum):
    PRIME     = "PRIME"
    SUB_PRIME = "SUB_PRIME"
    THIN_FILE = "THIN_FILE"

# --- Verification Source ---
class VerificationSource(str, enum.Enum):
    FIELD_OFFICER       = "FIELD_OFFICER"
    ACCOUNT_AGGREGATOR  = "ACCOUNT_AGGREGATOR"

# --- Verification Status ---
class VerificationStatus(str, enum.Enum):
    VERIFIED_CLEAN        = "VERIFIED_CLEAN"
    VERIFIED_WITH_VARIANCE= "VERIFIED_WITH_VARIANCE"
    FRAUD_DETECTED        = "FRAUD_DETECTED"
    UNREACHABLE           = "UNREACHABLE"
    MISSING_SECONDARY_CONTACT = "MISSING_SECONDARY_CONTACT"

# --- Vintage Artifact Type ---
class ArtifactType(str, enum.Enum):
    MUNICIPAL_LICENSE = "municipal_license"
    RENT_AGREEMENT    = "rent_agreement"
    MERCHANT_QR       = "merchant_qr"
    NONE              = "none"

# --- Counter Offer Action ---
class CounterOfferAction(str, enum.Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"

# --- Reprompt Type (ADR-025) ---
class RepromptType(str, enum.Enum):
    SECONDARY_CONTACT = "SECONDARY_CONTACT"

# --- Reprompt Validation Status (ADR-025) ---
class RepromptValidationStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED  = "FAILED"

# --- Scorecard Pass/Fail ---
class ScorecardVerdict(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"

# --- Co-Applicant Pathway ---
class CoApplicantPathway(str, enum.Enum):
    PERSON_A = "PERSON_A"   # Bureau-scored
    PERSON_B = "PERSON_B"   # Thin-file / field-verified
```

---

## 4. SQLAlchemy Models

**`db/base.py`**
```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

---

**`models/session.py`** — Core Application Session
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from models.enums import ApplicationState, LoanPurpose, LoanTerm, IncomeBracket, BureauGateStatus

class ApplicationSession(Base):
    """
    Root record. One row per loan application lifecycle.
    Owns the state machine cursor.
    """
    __tablename__ = "application_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    current_state: Mapped[ApplicationState] = mapped_column(
        SAEnum(ApplicationState), nullable=False, default=ApplicationState.INTAKE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Loan request fields (immutable after INTAKE submission)
    loan_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    loan_term: Mapped[LoanTerm] = mapped_column(SAEnum(LoanTerm), nullable=False)
    loan_purpose: Mapped[LoanPurpose] = mapped_column(SAEnum(LoanPurpose), nullable=False)
    income_bracket: Mapped[IncomeBracket] = mapped_column(SAEnum(IncomeBracket), nullable=False)

    # Bureau gate result (set during TRIAGE)
    bureau_gate_status: Mapped[BureauGateStatus | None] = mapped_column(
        SAEnum(BureauGateStatus), nullable=True
    )
    triage_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    primary_applicant: Mapped["ApplicantProfile"] = relationship(
        "ApplicantProfile",
        primaryjoin="and_(ApplicantProfile.session_id == ApplicationSession.id, "
                    "ApplicantProfile.is_co_applicant == False)",
        uselist=False, back_populates="session"
    )
    co_applicant: Mapped["ApplicantProfile | None"] = relationship(
        "ApplicantProfile",
        primaryjoin="and_(ApplicantProfile.session_id == ApplicationSession.id, "
                    "ApplicantProfile.is_co_applicant == True)",
        uselist=False
    )
    verifications: Mapped[list["VerificationRecord"]] = relationship(
        "VerificationRecord", back_populates="session"
    )
    state_events: Mapped[list["StateTransitionEvent"]] = relationship(
        "StateTransitionEvent", back_populates="session", order_by="StateTransitionEvent.occurred_at"
    )
    optimization_result: Mapped["OptimizationResult | None"] = relationship(
        "OptimizationResult", back_populates="session", uselist=False
    )
```

---

**`models/applicant.py`** — Primary and Co-Applicant Profiles
```python
import uuid
from sqlalchemy import String, Boolean, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

class ApplicantProfile(Base):
    """
    Stores both primary and co-applicant profiles in a single table.
    is_co_applicant flag discriminates between them.
    Nullable co-applicant fields are enforced at the application layer.
    """
    __tablename__ = "applicant_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    is_co_applicant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Intake data
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    national_id: Mapped[str] = mapped_column(String(12), nullable=False)    # PAN (10) or Aadhaar (12)
    pincode: Mapped[str] = mapped_column(String(6), nullable=False)

    # Canonical normalization outputs (ADR-022)
    canonical_verified_income: Mapped[int | None] = mapped_column(nullable=True)
    canonical_vintage_months: Mapped[int | None] = mapped_column(nullable=True)
    canonical_verification_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Co-applicant specific (ADR-025)
    co_app_canonical_verification_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    co_app_pathway: Mapped[str | None] = mapped_column(String(10), nullable=True)  # PERSON_A / PERSON_B

    # Bureau data (Person A only)
    cibil_score: Mapped[int | None] = mapped_column(nullable=True)
    national_id_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="primary_applicant", foreign_keys=[session_id])
```

---

**`models/verification.py`** — Verification Records and Artifact Hashes
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base
from models.enums import VerificationSource, VerificationStatus, ArtifactType

class VerificationRecord(Base):
    """
    One record per verification attempt. Multiple are possible within PENDING_VERIFICATION.
    Tamper evidence hashes are stored immutably.
    """
    __tablename__ = "verification_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Source and status
    verification_source: Mapped[VerificationSource] = mapped_column(SAEnum(VerificationSource), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus), nullable=False)

    # Verified financial data (exact integers — categorical brackets destroyed on entry)
    verified_monthly_cash_income: Mapped[int | None] = mapped_column(Integer, nullable=True)
    secondary_contact_number: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # Tamper evidence (ADR-025 §4)
    fo_visit_photo_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)   # SHA-256 hex
    tamper_evidence_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Vintage artifact
    artifact_type: Mapped[ArtifactType | None] = mapped_column(SAEnum(ArtifactType), nullable=True)
    artifact_issue_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    artifact_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)          # SHA-256 hex
    business_vintage_months_derived: Mapped[int | None] = mapped_column(Integer, nullable=True)

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="verifications")


class OptimizationResult(Base):
    """
    Written exactly once, after OPTIMIZATION completes.
    Immutable after creation.
    """
    __tablename__ = "optimization_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False, unique=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Scorecard metrics
    repayment_trust: Mapped[str] = mapped_column(String(4), nullable=False)     # PASS / FAIL
    available_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    emi_shortfall: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optimization outputs
    approved_loan_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_tenure: Mapped[int] = mapped_column(Integer, nullable=False)
    coapplicant_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    required_coapplicant_income_baseline: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Decision explanation
    decision_verdict: Mapped[str] = mapped_column(String(20), nullable=False)   # READY / NEARLY_READY / NOT_READY_YET
    primary_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    recovery_roadmap: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="optimization_result")
```

---

**`models/state_event.py`** — State Transition Audit Log
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("application_sessions.id"), nullable=False)
    from_state: Mapped[ApplicationState] = mapped_column(SAEnum(ApplicationState), nullable=False)
    to_state: Mapped[ApplicationState] = mapped_column(SAEnum(ApplicationState), nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)    # e.g. "triage_math_pass"
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)            # "SYSTEM" or API route

    session: Mapped["ApplicationSession"] = relationship("ApplicationSession", back_populates="state_events")
```

---

## 5. Database Relationships

```
ApplicationSession (1)
  ├── ApplicantProfile (1)   [primary, is_co_applicant=False]
  ├── ApplicantProfile (0..1)[co-applicant, is_co_applicant=True]
  ├── VerificationRecord (1..N)
  ├── StateTransitionEvent (1..N) [append-only]
  └── OptimizationResult (0..1)   [written exactly once]
```

---

## 6. Constraint Definitions

All constraints enforce ADR-024 bounds at the database level, independently of application-layer validation:

```sql
-- Loan amount product bounds (ADR-024 §2)
ALTER TABLE application_sessions
  ADD CONSTRAINT chk_loan_amount_bounds
  CHECK (loan_amount >= 1000 AND loan_amount <= 500000);

-- Loan term must be a valid product term (ADR-024 §3.2)
ALTER TABLE application_sessions
  ADD CONSTRAINT chk_loan_term_valid
  CHECK (loan_term IN (12, 18, 24, 36, 48, 60));

-- Pincode must be exactly 6 digits
ALTER TABLE applicant_profiles
  ADD CONSTRAINT chk_pincode_format
  CHECK (pincode ~ '^[0-9]{6}$');

-- Vintage months cannot be negative (ADR-024 §7)
ALTER TABLE verification_records
  ADD CONSTRAINT chk_vintage_months_nonnegative
  CHECK (business_vintage_months_derived IS NULL OR business_vintage_months_derived >= 0);

-- Verified income cannot be negative
ALTER TABLE verification_records
  ADD CONSTRAINT chk_verified_income_nonnegative
  CHECK (verified_monthly_cash_income IS NULL OR verified_monthly_cash_income >= 0);

-- Optimization: approved amount must be within product bounds
ALTER TABLE optimization_results
  ADD CONSTRAINT chk_approved_amount_bounds
  CHECK (approved_loan_amount >= 1000 AND approved_loan_amount <= 500000);

-- Optimization: approved tenure must be within product bounds
ALTER TABLE optimization_results
  ADD CONSTRAINT chk_approved_tenure_bounds
  CHECK (approved_tenure >= 12 AND approved_tenure <= 60);
```

---

## 7. Alembic Migration

**`alembic/versions/001_v2_init.py`**
```python
"""v2_init: Phase 1 schema

Revision ID: 001_v2_init
Revises: —
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa

revision = "001_v2_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. application_sessions
    op.create_table(
        "application_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("current_state", sa.String(30), nullable=False, server_default="INTAKE"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("loan_amount", sa.Integer, nullable=False),
        sa.Column("loan_term", sa.Integer, nullable=False),
        sa.Column("loan_purpose", sa.String(30), nullable=False),
        sa.Column("income_bracket", sa.String(15), nullable=False),
        sa.Column("bureau_gate_status", sa.String(15), nullable=True),
        sa.Column("triage_pass", sa.Boolean, nullable=True),
        sa.CheckConstraint("loan_amount >= 1000 AND loan_amount <= 500000", name="chk_loan_amount_bounds"),
        sa.CheckConstraint("loan_term IN (12, 18, 24, 36, 48, 60)", name="chk_loan_term_valid"),
    )

    # 2. applicant_profiles
    op.create_table(
        "applicant_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False),
        sa.Column("is_co_applicant", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("national_id", sa.String(12), nullable=False),
        sa.Column("pincode", sa.String(6), nullable=False),
        sa.Column("canonical_verified_income", sa.Integer, nullable=True),
        sa.Column("canonical_vintage_months", sa.Integer, nullable=True),
        sa.Column("canonical_verification_pass", sa.Boolean, nullable=True),
        sa.Column("co_app_canonical_verification_pass", sa.Boolean, nullable=True),
        sa.Column("co_app_pathway", sa.String(10), nullable=True),
        sa.Column("cibil_score", sa.Integer, nullable=True),
        sa.Column("national_id_match_score", sa.Float, nullable=True),
    )

    # 3. verification_records
    op.create_table(
        "verification_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("received_at", sa.DateTime, nullable=False),
        sa.Column("verification_source", sa.String(25), nullable=False),
        sa.Column("verification_status", sa.String(30), nullable=False),
        sa.Column("verified_monthly_cash_income", sa.Integer, nullable=True),
        sa.Column("secondary_contact_number", sa.String(15), nullable=True),
        sa.Column("fo_visit_photo_hash", sa.String(64), nullable=True),
        sa.Column("tamper_evidence_pass", sa.Boolean, nullable=True),
        sa.Column("artifact_type", sa.String(25), nullable=True),
        sa.Column("artifact_issue_date", sa.Date, nullable=True),
        sa.Column("artifact_hash", sa.String(64), nullable=True),
        sa.Column("business_vintage_months_derived", sa.Integer, nullable=True),
        sa.CheckConstraint(
            "business_vintage_months_derived IS NULL OR business_vintage_months_derived >= 0",
            name="chk_vintage_months_nonnegative"
        ),
    )

    # 4. optimization_results
    op.create_table(
        "optimization_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False, unique=True),
        sa.Column("computed_at", sa.DateTime, nullable=False),
        sa.Column("repayment_trust", sa.String(4), nullable=False),
        sa.Column("available_capacity", sa.Integer, nullable=False),
        sa.Column("emi_shortfall", sa.Integer, nullable=False),
        sa.Column("approved_loan_amount", sa.Integer, nullable=False),
        sa.Column("approved_tenure", sa.Integer, nullable=False),
        sa.Column("coapplicant_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("required_coapplicant_income_baseline", sa.Integer, nullable=True),
        sa.Column("decision_verdict", sa.String(20), nullable=False),
        sa.Column("primary_reason", sa.String(500), nullable=False),
        sa.Column("recovery_roadmap", sa.String(2000), nullable=True),
        sa.CheckConstraint(
            "approved_loan_amount >= 1000 AND approved_loan_amount <= 500000",
            name="chk_approved_amount_bounds"
        ),
        sa.CheckConstraint(
            "approved_tenure >= 12 AND approved_tenure <= 60",
            name="chk_approved_tenure_bounds"
        ),
    )

    # 5. state_transition_events
    op.create_table(
        "state_transition_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False),
        sa.Column("from_state", sa.String(30), nullable=False),
        sa.Column("to_state", sa.String(30), nullable=False),
        sa.Column("trigger_event", sa.String(100), nullable=False),
        sa.Column("occurred_at", sa.DateTime, nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
    )

    # Indexes
    op.create_index("ix_sessions_state", "application_sessions", ["current_state"])
    op.create_index("ix_applicants_session", "applicant_profiles", ["session_id"])
    op.create_index("ix_verifications_session", "verification_records", ["session_id"])
    op.create_index("ix_events_session_time", "state_transition_events", ["session_id", "occurred_at"])


def downgrade() -> None:
    op.drop_table("state_transition_events")
    op.drop_table("optimization_results")
    op.drop_table("verification_records")
    op.drop_table("applicant_profiles")
    op.drop_table("application_sessions")
```

---

## 8. Pydantic Schemas

**`schemas/enums.py`** — mirrors `models/enums.py` exactly for API-layer use.

```python
from models.enums import (
    ApplicationState, IncomeBracket, LoanTerm, LoanPurpose,
    BureauGateStatus, VerificationSource, VerificationStatus,
    ArtifactType, CounterOfferAction, RepromptType,
    RepromptValidationStatus, ScorecardVerdict, CoApplicantPathway,
)

__all__ = [
    "ApplicationState", "IncomeBracket", "LoanTerm", "LoanPurpose",
    "BureauGateStatus", "VerificationSource", "VerificationStatus",
    "ArtifactType", "CounterOfferAction", "RepromptType",
    "RepromptValidationStatus", "ScorecardVerdict", "CoApplicantPathway",
]
```

---

## 9. Migration Order

The following migration sequence must be strictly respected to honor foreign key constraints:

```
Step 1:  application_sessions       (root, no foreign keys)
Step 2:  applicant_profiles         (FKs: application_sessions)
Step 3:  verification_records       (FKs: application_sessions)
Step 4:  optimization_results       (FKs: application_sessions, unique constraint)
Step 5:  state_transition_events    (FKs: application_sessions, append-only)
Step 6:  indexes                    (after all tables)
```

---

## 10. Phase 1 Test Plan

**`tests/phase1/test_enums.py`**
| Test | Assertion |
| :--- | :--- |
| `test_income_bracket_exhaustive` | All 6 brackets defined; no others accepted |
| `test_loan_term_exhaustive` | Exactly `{12, 18, 24, 36, 48, 60}` valid |
| `test_loan_purpose_exhaustive` | All 7 purposes defined; no others accepted |
| `test_application_state_exhaustive` | All 9 states defined including `PENDING_REPROMPT` |
| `test_counter_offer_action_binary` | Only ACCEPT and REJECT valid |
| `test_reprompt_type_singleton` | Only SECONDARY_CONTACT valid |

**`tests/phase1/test_models.py`**
| Test | Assertion |
| :--- | :--- |
| `test_session_defaults_to_intake` | `current_state == INTAKE` on creation |
| `test_loan_amount_floor_constraint` | `loan_amount = 999` raises `IntegrityError` |
| `test_loan_amount_ceiling_constraint` | `loan_amount = 500001` raises `IntegrityError` |
| `test_loan_term_invalid_constraint` | `loan_term = 13` raises `IntegrityError` |
| `test_vintage_months_negative_constraint` | `business_vintage_months_derived = -1` raises `IntegrityError` |
| `test_optimization_result_unique_per_session` | Second insert for same `session_id` raises `IntegrityError` |
| `test_state_events_append_only` | `UPDATE` on `state_transition_events` raises `ProgrammingError` |
| `test_coapplicant_nullable` | Session with no co-applicant row saves successfully |

**`tests/phase1/test_migrations.py`**
| Test | Assertion |
| :--- | :--- |
| `test_migration_upgrade_clean` | `alembic upgrade head` completes with zero errors on empty DB |
| `test_migration_downgrade_clean` | `alembic downgrade base` restores empty schema with no orphaned tables |
| `test_migration_idempotent` | Running `upgrade head` twice produces no change |
