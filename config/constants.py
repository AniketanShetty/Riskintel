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
