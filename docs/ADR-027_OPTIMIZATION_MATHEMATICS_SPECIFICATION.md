# ADR-027: Optimization Mathematics Specification

**Date:** 2026-06-13
**Status:** PROPOSED
**Resolves:** Blockers identified in `PHASE2_AUDIT_REPORT.md` regarding deterministic algebra and floating-point drift.

---

## 1. Context

RiskIntel V2 demands absolute determinism. Two identical payloads must mathematically produce the exact same final database state. However, the Phase 2 Audit identified that `ADR-023` and `ADR-024` failed to explicitly define the compounding frequencies, algebraic rounding rules, and loop mechanisms required for the Optimization Engine's PMT calculations. Without these rules, engineers would inadvertently introduce floating-point drift and divergent logic trees, destroying the persistence layer's integrity.

## 2. Interest Compounding Definition

**Context:** The `SYSTEM_BASE_INTEREST_RATE` is defined as `0.24` (24% APR). The compounding frequency dictates the actual EMI burden.
**Options Considered:**
1. Exact daily compounding (high precision, complex calendar leap-year math).
2. Monthly compounding (standard retail banking, deterministic).
**Decision:** We will use **strictly monthly compounding**. The period rate `r` is explicitly defined as `SYSTEM_BASE_INTEREST_RATE / 12` (i.e., `0.02`). 
**Consequences:** Calendar shifts and leap years are mathematically ignored for affordability calculations, guaranteeing absolute idempotency.

## 3. EMI Rounding Policy & Determinism Guarantee

**Context:** Native IEEE 754 floating-point arithmetic (`float`) causes micro-variances across different CPU architectures.
**Decision:** 
1. **No Floats:** The Optimization Engine must strictly use the native Python `decimal.Decimal` module initialized with a 6-place precision context for all intermediate steps.
2. **Rounding Rule:** The final EMI is mathematically forced to round **UP** (ceiling) to the nearest whole integer (`ROUND_CEILING`).
**Tradeoffs:** Ceiling the EMI slightly overestimates the borrower's burden by a few paise, but it guarantees absolute conservative safety against `available_capacity`.
**Consequences:** EMI outputs are returned exclusively as integers.

## 4. PMT Formula Definition & Bifurcation

The system mandates a strict bifurcation between the initial requested burden and the final approved burden to prevent floating-point drift:
1. `target_emi`: The exact mathematical burden of the user's initially requested terms (before optimization).
2. `contract_emi`: The exact mathematical burden of the final, stretched, or reduced terms (the actual counter-offer).

Both values must be persisted physically and computed using the exact same formula:

```python
from decimal import Decimal, ROUND_CEILING

def calculate_target_emi(principal: int, annual_rate: float, tenure_months: int) -> int:
    P = Decimal(str(principal))
    r = Decimal(str(annual_rate)) / Decimal('12')
    n = Decimal(str(tenure_months))
    
    # Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    compound_factor = (Decimal('1') + r) ** n
    emi = P * r * compound_factor / (compound_factor - Decimal('1'))
    
    # Strict integer ceiling
    return int(emi.to_integral_value(rounding=ROUND_CEILING))
```

## 5. Tenure Stretching Algorithm

**Context:** When `target_emi > total_available_capacity`, the system must "stretch the tenure". `ADR-021` was ambiguous on whether to jump instantly to 60 months or increment gradually.
**Options Considered:**
1. Jump to `SYSTEM_MAX_TENURE` (60) immediately (Fast O(1), but maximizes interest burden unfairly).
2. Step-wise increment (+1 month) until affordable.
**Decision:** **Step-wise increment**. The Engine will iterate in `+1` month steps from the requested `loan_term` up to `SYSTEM_MAX_TENURE` (60). It will evaluate `calculate_target_emi` at each step. It halts and returns the *first* tenure that achieves `target_emi <= total_available_capacity`.
**Consequences:** Protects the borrower from maximum interest while fulfilling the mathematical constraint. Requires an execution loop bounded by a maximum of 48 iterations (12 to 60).

## 6. Loan Reduction Algorithm

**Context:** If tenure is maximized to 60 months and the `target_emi` still exceeds `total_available_capacity` (and `loan_purpose` is `DIVISIBLE`), the principal must be reduced.
**Options Considered:**
1. Decrement principal in loops of 1,000 INR.
2. Algebraic Present Value (PV) Inverse.
**Decision:** **Algebraic PV Inverse**, followed by a `FLOOR` to the nearest 1,000 INR.
Instead of looping, we instantly calculate the maximum principal the borrower can sustain given the `total_available_capacity` at `SYSTEM_MAX_TENURE`.

```python
from decimal import Decimal, ROUND_FLOOR

def calculate_reduced_principal(available_capacity: int, annual_rate: float, tenure_months: int) -> int:
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
```

## 7. Counter-Offer Generation Rules

A counter-offer (`NEARLY_READY`) is only legally emitted if:
1. `reduced_principal >= SYSTEM_MIN_LOAN_AMOUNT` (1000 INR).
2. If `reduced_principal < 1000`, the math fails and throws an immediate terminal `NOT_READY_YET`.

## 8. Worked Numerical Examples

**Scenario 1: Tenure Stretch Success**
* Input: Requested Principal = 50,000. Tenure = 12. Rate = 0.24. Capacity = 3,000.
* Initial EMI at 12m = 4,728 (Fails, 4728 > 3000).
* Stretch Loop:
  * ... at 18m = 3,337 (Fails)
  * ... at 24m = 2,644 (Passes! 2644 <= 3000)
* Result: Counter-Offer = 50,000 at 24 months.

**Scenario 2: Principal Reduction Required**
* Input: Requested Principal = 100,000. Tenure = 24. Rate = 0.24. Capacity = 2,000. Purpose = DIVISIBLE.
* Stretch hits 60m max. EMI at 60m = 2,877 (Fails, 2877 > 2000).
* Inverse PV: Max Principal for 2,000 EMI at 60m = ~69,522.
* Floor to 1000s: 69,000.
* Re-verify: EMI for 69,000 at 60m = 1,985 (Passes!).
* Result: Counter-Offer = 69,000 at 60 months.

## 9. Edge Cases

1. **Zero or Negative Capacity:** If `total_available_capacity <= 0` prior to optimization, skip all math. If purpose is DIVISIBLE, attempt `coapplicant_required` pipeline immediately. If INDIVISIBLE, return `NOT_READY_YET`.
2. **Exactly Equivalent EMI:** If `target_emi == total_available_capacity`, the Engine cleanly passes to `READY` without stretching.

## 10. Required Test Cases

Engineers must implement pytest parameterized tests explicitly asserting these exact inputs equal these exact integer outputs to pass CI:
1. `test_pmt_standard`: P=50000, r=0.24, n=12 -> asserts EMI == 4728
2. `test_pmt_rounding`: P=1000, r=0.24, n=12 -> asserts EMI == 95 (forces testing of ROUND_CEILING logic)
3. `test_pv_reduction`: Capacity=2000, r=0.24, n=60 -> asserts Reduced Principal == 69000
4. `test_min_principal_breach`: Capacity=25, r=0.24, n=60 -> Reduced Principal < 1000 -> asserts `NOT_READY_YET` transition.
