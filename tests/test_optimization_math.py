import pytest
from services.optimization_math import (
    calculate_target_emi,
    calculate_reduced_principal,
    optimize_loan
)

def test_pmt_standard():
    # Scenario 1 from ADR-027 (Section 10.1): P=50000, r=0.24, n=12 -> EMI == 4728
    emi = calculate_target_emi(50000, 0.24, 12)
    assert emi == 4728

def test_pmt_rounding():
    # Scenario 2 from ADR-027 (Section 10.2): P=1000, r=0.24, n=12 -> EMI == 95 
    # Strictly forces testing of ROUND_CEILING logic vs standard floats
    emi = calculate_target_emi(1000, 0.24, 12)
    assert emi == 95

def test_pv_reduction():
    # Scenario 3 from ADR-027 (Section 10.3): Capacity=2000, r=0.24, n=60 -> Reduced Principal == 69000
    reduced = calculate_reduced_principal(2000, 0.24, 60)
    assert reduced == 69000

def test_min_principal_breach():
    # Scenario 4 from ADR-027 (Section 10.4): Capacity=25, r=0.24, n=60 -> NOT_READY_YET
    result = optimize_loan(principal=50000, annual_rate=0.24, tenure_months=12, available_capacity=25, is_divisible=True)
    assert result.status == 'NOT_READY_YET'
    assert result.approved_loan_amount is None
    assert result.contract_emi == 0

def test_optimize_loan_stretch_success():
    # Scenario 1 Full Optimization (Section 8)
    # Requested Principal = 50,000. Tenure = 12. Rate = 0.24. Capacity = 3,000
    # Expected: Stretches to 21 months, EMI=2940 (first tenure where EMI <= 3000)
    result = optimize_loan(principal=50000, annual_rate=0.24, tenure_months=12, available_capacity=3000, is_divisible=True)
    assert result.status == 'NEARLY_READY'
    assert result.target_emi == 4728
    assert result.contract_emi == 2940
    assert result.approved_loan_amount == 50000
    assert result.approved_tenure == 21
    assert result.tenure_stretched is True
    assert result.reduced_principal is False

def test_optimize_loan_reduction_required():
    # Scenario 2 Full Optimization (Section 8)
    # Requested Principal = 100,000. Tenure = 24. Rate = 0.24. Capacity = 2,000. DIVISIBLE.
    # Result: Counter-Offer = 69,000 at 60 months.
    result = optimize_loan(principal=100000, annual_rate=0.24, tenure_months=24, available_capacity=2000, is_divisible=True)
    assert result.status == 'NEARLY_READY'
    assert result.approved_loan_amount == 69000
    assert result.approved_tenure == 60
    assert result.contract_emi == 1985
    assert result.reduced_principal is True
    assert result.tenure_stretched is True

def test_zero_capacity_divisible():
    # Edge Case 1 (Section 9.1): Zero capacity, Divisible
    result = optimize_loan(principal=50000, annual_rate=0.24, tenure_months=12, available_capacity=0, is_divisible=True)
    assert result.status == 'NOT_READY_YET'
    assert result.coapplicant_required is True
    assert result.target_emi == 4728

def test_zero_capacity_indivisible():
    # Edge Case 1 (Section 9.1): Zero capacity, Indivisible
    result = optimize_loan(principal=50000, annual_rate=0.24, tenure_months=12, available_capacity=0, is_divisible=False)
    assert result.status == 'NOT_READY_YET'
    assert result.target_emi == 4728

def test_exact_capacity():
    # Edge Case 2 (Section 9.2): Exactly Equivalent EMI
    result = optimize_loan(principal=50000, annual_rate=0.24, tenure_months=12, available_capacity=4728, is_divisible=False)
    assert result.status == 'READY'
    assert result.target_emi == 4728
    assert result.approved_tenure == 12

def test_indivisible_reduction_fail():
    # Indivisible loans cannot have their principal reduced. If tenure maxes out, it must fail.
    result = optimize_loan(principal=100000, annual_rate=0.24, tenure_months=24, available_capacity=2000, is_divisible=False)
    assert result.status == 'NOT_READY_YET'
    assert result.approved_loan_amount is None
    assert result.approved_tenure is None
