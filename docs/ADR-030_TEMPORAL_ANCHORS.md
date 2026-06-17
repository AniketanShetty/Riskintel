# ADR-030: Temporal Anchors and Date Math Standards

**Date:** 2026-06-13
**Status:** PROPOSED
**Resolves:** Blockers identified in Phase 2 Audit concerning chronological drift, age idempotency, and retry windows.

---

## 1. Context

RiskIntel V2 enforces 100% deterministic re-execution. If a compliance auditor re-evaluates an application three years after it was submitted, the Optimization Engine must yield the exact same `age`, `business_vintage_months`, and `retry_deadline` as the day it was originally run. 

The use of dynamic clock calls (e.g., `datetime.now()` or `CURRENT_TIMESTAMP`) inside business logic fundamentally destroys chronological determinism. This ADR standardizes the global mathematical anchors and truncation algorithms for all temporal calculations.

## 2. The Global Temporal Anchor (`T0`)

**Decision:** 
The supreme chronometric anchor for all structural evaluation engines is explicitly defined as `application_sessions.created_at`. 

*   **Banned Practice:** Backend engines (Readiness, Trust, Optimization) are strictly banned from importing or calling `datetime.now()`, `datetime.today()`, or `func.now()`.
*   **Consequence:** The entire mathematical lifecycle of the loan application is frozen in time at the exact millisecond the `INTAKE` payload was committed to the persistence layer.

## 3. Deterministic Age Calculation

**Context:** The `age` logic (`>= 18 AND <= 70`) must perfectly handle leap years and ensure re-execution safety.
**Decision:** Age is calculated mathematically by evaluating the exact differential between the KYC Date of Birth (DOB) and `T0`.

**Formula:**
```python
def calculate_age(kyc_dob: date, session_created_at: datetime) -> int:
    anchor_date = session_created_at.date()
    
    # Calculate exact year differential, subtracting 1 if the birthday hasn't occurred yet in the anchor year
    had_birthday = (anchor_date.month, anchor_date.day) >= (kyc_dob.month, kyc_dob.day)
    age_years = anchor_date.year - kyc_dob.year - (0 if had_birthday else 1)
    
    return age_years
```

## 4. Deterministic Business Vintage Calculation

**Context:** Formally absorbing the month-truncation rule outlined in `ADR-024` and strictly tying it to `T0`. Day-of-the-month variance is mathematically destroyed.

**Formula:**
```python
def calculate_business_vintage_months(issue_date: date, session_created_at: datetime) -> int:
    anchor_date = session_created_at.date()
    
    months_diff = ((anchor_date.year - issue_date.year) * 12) + (anchor_date.month - issue_date.month)
    
    # Negative drift protection (e.g., artifact issued after application date)
    return max(0, months_diff)
```

## 5. Retry-Window Anchoring (The 14-Day Limit)

**Context:** The Constitution mandates a "14-day retry window (max 2 attempts)" for the `UNREACHABLE` verification status. Since verification occurs asynchronously after `T0`, anchoring to `T0` would unfairly punish applications delayed in the Triage queue.
**Decision:** The 14-day TTL is anchored strictly to the `state_transition_events.occurred_at` timestamp of the *first* time the session transitioned to `PENDING_VERIFICATION`.

**Execution Logic:**
1. Upon an `UNREACHABLE` webhook, query `state_transition_events` for `to_state == 'PENDING_VERIFICATION'`.
2. Extract the `occurred_at` timestamp (`T_verif`).
3. If `webhook_received_at > T_verif + timedelta(days=14)`, automatically lock the session and force transition to `NOT_READY_YET`.

## 6. Worked Examples & Edge Cases

**Scenario 1: Leap Year Birthday Boundary**
* `kyc_dob` = 2004-02-29
* `session_created_at` = 2022-02-28 (Not a leap year).
* Calculation: `(2, 28) >= (2, 29)` is `False`.
* Age: `2022 - 2004 - 1` = 17. The applicant is correctly rejected.

**Scenario 2: Audit Re-Execution**
* Real-world time: 2026-06-13.
* `session_created_at` = 2023-01-10.
* `kyc_dob` = 1990-05-15.
* The system evaluates age as of `2023-01-10` (Age = 32). It completely ignores the 2026 execution clock, preserving perfect historical determinism.

**Scenario 3: Paradoxical Vintage Dates**
* `session_created_at` = 2026-03-01.
* Field Officer enters `vintage_artifact_issue_date` = 2026-05-10.
* Calculation: `(2026 - 2026)*12 + (3 - 5)` = -2.
* Floor correction: `max(0, -2)` = 0. Applicant correctly hits the `business_vintage_months < 24` Hard Reject.

## 7. Pytest Acceptance Criteria

The following unit tests are strictly mandated for CI passage:
1. `test_age_leap_year_boundary`: Asserts that an applicant born on Feb 29 evaluated on non-leap-year Feb 28 does not gain a year prematurely.
2. `test_idempotent_reexecution`: Evaluates the same payload with a mocked system clock shifted forward 5 years; asserts that the calculated age and vintage remain perfectly identical.
3. `test_vintage_month_truncation`: Asserts `2026-05-01` to `2026-05-31` evaluates as exactly `0` months, destroying day-of-month impact.
4. `test_retry_window_expiration`: Mocks a webhook arriving at `T_verif + 14 days, 1 second`; asserts a strict `NOT_READY_YET` transition routing.
