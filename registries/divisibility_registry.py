# RiskIntel V2: Divisibility Registry
from models.enums import LoanPurpose, DivisibilityClass

DIVISIBILITY_REGISTRY: dict[LoanPurpose, DivisibilityClass] = {
    LoanPurpose.MEDICAL: DivisibilityClass.INDIVISIBLE,
    LoanPurpose.EDUCATION: DivisibilityClass.INDIVISIBLE,
    LoanPurpose.DEBT_CONSOLIDATION: DivisibilityClass.INDIVISIBLE,
    LoanPurpose.TWO_WHEELER: DivisibilityClass.INDIVISIBLE,
    LoanPurpose.WORKING_CAPITAL: DivisibilityClass.DIVISIBLE,
    LoanPurpose.HOME_REPAIR: DivisibilityClass.DIVISIBLE,
    LoanPurpose.WEDDING: DivisibilityClass.DIVISIBLE,
}

def is_divisible(purpose: LoanPurpose) -> bool:
    """Returns True if the loan product allows amount reduction during counter-offers."""
    return DIVISIBILITY_REGISTRY[purpose] == DivisibilityClass.DIVISIBLE
