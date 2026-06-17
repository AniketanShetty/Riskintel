from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from dataclasses import dataclass

SYSTEM_MAX_TENURE = 60
SYSTEM_MIN_LOAN_AMOUNT = 1000

@dataclass
class OptimizationOutput:
    status: str  # 'READY', 'NEARLY_READY', 'NOT_READY_YET', 'COAPPLICANT_REQUIRED'
    target_emi: int
    contract_emi: int
    approved_loan_amount: int | None
    approved_tenure: int | None
    reduced_principal: bool = False
    tenure_stretched: bool = False
    coapplicant_required: bool = False

def calculate_target_emi(principal: int, annual_rate: float, tenure_months: int) -> int:
    """Calculates the exact integer EMI strictly using ROUND_CEILING."""
    P = Decimal(str(principal))
    r = Decimal(str(annual_rate)) / Decimal('12')
    n = Decimal(str(tenure_months))
    
    # Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    compound_factor = (Decimal('1') + r) ** n
    emi = P * r * compound_factor / (compound_factor - Decimal('1'))
    
    # Strict integer ceiling
    return int(emi.to_integral_value(rounding=ROUND_CEILING))

def calculate_reduced_principal(available_capacity: int, annual_rate: float, tenure_months: int) -> int:
    """Calculates the maximum supported principal explicitly rounded down to the nearest 1000."""
    EMI = Decimal(str(available_capacity))
    r = Decimal(str(annual_rate)) / Decimal('12')
    n = Decimal(str(tenure_months))
    
    # Formula: P = EMI * ((1+r)^n - 1) / (r * (1+r)^n)
    compound_factor = (Decimal('1') + r) ** n
    max_principal = EMI * (compound_factor - Decimal('1')) / (r * compound_factor)
    
    # Floor to nearest 1000 INR step
    max_principal_int = int(max_principal.to_integral_value(rounding=ROUND_FLOOR))
    reduced_principal = (max_principal_int // 1000) * 1000
    
    return reduced_principal

def optimize_loan(principal: int, annual_rate: float, tenure_months: int, available_capacity: int, is_divisible: bool) -> OptimizationOutput:
    """Core Mathematical Optimization Engine executing ADR-027 limits."""
    
    # Edge Case 1: Zero or Negative Capacity
    if available_capacity <= 0:
        if is_divisible:
            return OptimizationOutput(
                status='NOT_READY_YET',
                target_emi=calculate_target_emi(principal, annual_rate, tenure_months),
                contract_emi=0, approved_loan_amount=None, approved_tenure=None,
                coapplicant_required=True
            )
        else:
            return OptimizationOutput(
                status='NOT_READY_YET',
                target_emi=calculate_target_emi(principal, annual_rate, tenure_months),
                contract_emi=0, approved_loan_amount=None, approved_tenure=None
            )
            
    # Calculate initial target EMI
    target_emi = calculate_target_emi(principal, annual_rate, tenure_months)
    
    # Fast path: Affordable instantly
    if target_emi <= available_capacity:
        return OptimizationOutput(
            status='READY',
            target_emi=target_emi,
            contract_emi=target_emi,
            approved_loan_amount=principal,
            approved_tenure=tenure_months
        )
        
    # Stretch Tenure Loop (+1 step-wise)
    for t in range(tenure_months + 1, SYSTEM_MAX_TENURE + 1):
        test_emi = calculate_target_emi(principal, annual_rate, t)
        if test_emi <= available_capacity:
            return OptimizationOutput(
                status='NEARLY_READY',
                target_emi=target_emi,
                contract_emi=test_emi,
                approved_loan_amount=principal,
                approved_tenure=t,
                tenure_stretched=True
            )
            
    # Maximum stretch still fails
    if not is_divisible:
        return OptimizationOutput(
            status='NOT_READY_YET',
            target_emi=target_emi,
            contract_emi=calculate_target_emi(principal, annual_rate, SYSTEM_MAX_TENURE),
            approved_loan_amount=None,
            approved_tenure=None,
            tenure_stretched=True
        )
        
    # Principal Reduction (Inverse PV)
    reduced_principal = calculate_reduced_principal(available_capacity, annual_rate, SYSTEM_MAX_TENURE)
    
    if reduced_principal < SYSTEM_MIN_LOAN_AMOUNT:
        return OptimizationOutput(
            status='NOT_READY_YET',
            target_emi=target_emi,
            contract_emi=0,
            approved_loan_amount=None,
            approved_tenure=None
        )
        
    # Recalculate final contract EMI safely with rounding constraints
    final_contract_emi = calculate_target_emi(reduced_principal, annual_rate, SYSTEM_MAX_TENURE)
    
    return OptimizationOutput(
        status='NEARLY_READY',
        target_emi=target_emi,
        contract_emi=final_contract_emi,
        approved_loan_amount=reduced_principal,
        approved_tenure=SYSTEM_MAX_TENURE,
        tenure_stretched=True,
        reduced_principal=True
    )
