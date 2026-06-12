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
