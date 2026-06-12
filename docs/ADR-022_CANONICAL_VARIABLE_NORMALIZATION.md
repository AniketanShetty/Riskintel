# ADR-022: Canonical Variable Normalization Layer

## 1. Architectural Purpose
**Context:** The current architecture suffers from severe branch-merging failures. Specifically, the digital (Person A) and physical (Person B) verification pathways produce disjoint, source-specific variables (e.g., `verified_income` vs `verified_monthly_cash_income`). Downstream business logic engines (Scorecard Formulas, Decision Tables, Optimization) currently attempt to consume single variables that do not exist for both pathways.

**Purpose:** This ADR introduces a mandatory Canonical Variable Normalization Layer executing immediately after Verification. Optimization, decision tables, and APIs must NEVER consume source-specific fields directly. By mathematically enforcing a canonical data model, we guarantee that all downstream rule engines receive deterministic, guaranteed inputs regardless of whether the applicant went through an Account Aggregator or Field Officer pathway.

## 2. Canonical Variable Registry

| Source Variable (Person A / AA) | Source Variable (Person B / FO) | Canonical Variable |
|---------------------------------|---------------------------------|--------------------|
| `verified_income` | `verified_monthly_cash_income` | `canonical_verified_income` |
| `account_history_months` | `business_vintage_months` | `canonical_vintage_months` |
| `national_id_match_score` | `verification_status` | `canonical_verification_pass` |
| `Base_Line` / `Base_Subsistence_Line` | `BASE_RURAL_LINE` | `SYSTEM_BASE_SUBSISTENCE_LINE` |

## 3. Income Normalization

The Affordability Index must strictly consume `canonical_verified_income`.

```text
canonical_verified_income = 
    IF (Pathway == Person_A) THEN verified_income
    ELSE IF (Pathway == Person_B) THEN verified_monthly_cash_income
    ELSE THROW Fatal_Error
```
**Rules:**
- **Precedence:** The engine checks pathway flags. There is no mathematical fallback between them since they are mutually exclusive.
- **Null Handling:** A null value instantly fails schema validation at the Normalization Layer.
- **Validation:** Must be an integer >= 0.

## 4. Vintage Normalization

Livelihood Resilience and Verification Audit API responses must strictly consume `canonical_vintage_months`.

```text
canonical_vintage_months = 
    IF (Pathway == Person_A) THEN account_history_months
    ELSE IF (Pathway == Person_B) THEN business_vintage_months
    ELSE THROW Fatal_Error
```
**Rules:**
- **Validation:** Must be an integer >= 0.
- **Negative-Value Handling:** If date parsing derives a negative number, it mathematically `FLOOR`s to 0.
- **Fraud Handling:** If `vintage_artifact_type` == `none` or `ARTIFACT_MISSING`, the canonical value defaults to 0.

## 5. Verification Strength Normalization

The Decision Table must strictly consume `canonical_verification_pass`.

```text
canonical_verification_pass = 
    IF (Pathway == Person_A) THEN 
        (national_id_match_score >= 0.85) AND (AA_Pull == SUCCESS)
    ELSE IF (Pathway == Person_B) THEN 
        (verification_status IN [VERIFIED_CLEAN, VERIFIED_WITH_VARIANCE])
    ELSE THROW Fatal_Error
```
This produces a universal Boolean, resolving the `DECISION_TABLE.md` gap where Person A's digital fraud check was entirely bypassed.

## 6. Consumer Ownership Matrix

| Canonical Variable | Consumed By |
|-------------------|-------------|
| `canonical_verified_income` | `SCORECARD_FORMULAS.md` (Affordability) |
| `canonical_vintage_months` | `SCORECARD_FORMULAS.md` (Livelihood), `API_CONTRACTS.md` (Verification Audit) |
| `canonical_verification_pass`| `DECISION_TABLE.md` (State Transition) |
| `SYSTEM_BASE_SUBSISTENCE_LINE` | `SCORECARD_FORMULAS.md`, `RISKINTEL_V2_CONSTITUTION.md`, `DATA_DICTIONARY.md` |

## 7. Repository Refactoring Plan

**1. docs/output_specs/SCORECARD_FORMULAS.md**
- **Section:** 2. Affordability Index & 3. Livelihood Resilience
- **Replacement:** Replace `verified_income` with `canonical_verified_income`. Replace `business_vintage_months` with `canonical_vintage_months`.
- **Rationale:** Ensures formulas do not crash when processing Person B (cash income) or Person A (AA history).

**2. docs/output_specs/API_CONTRACTS.md**
- **Section:** `POST /api/v2/verification_complete` Response
- **Replacement:** Replace `business_vintage_months_derived` with `canonical_vintage_months`.
- **Rationale:** The API must return the normalized data since Person A produces `account_history_months`.

**3. docs/DECISION_TABLE.md**
- **Section:** Entire Table Header
- **Replacement:** Replace `FO Verification` column with `canonical_verification_pass`.
- **Rationale:** Normalizes Person A and Person B fraud checks into a universal Boolean column.

**4. docs/output_specs/DATA_DICTIONARY.md**
- **Section:** 4. Derived & Bureau Fields
- **Replacement:** Insert Canonical Variables list. Unify baseline constant to `SYSTEM_BASE_SUBSISTENCE_LINE`.
- **Rationale:** Establishes the authoritative schema for normalized objects.

## 8. Validation

1. **Branch-Merging Test Cases:** Assert that an `account_history_months: 26` perfectly matches a `business_vintage_months: 26` at the normalization output.
2. **Person A Flow:** Pass a webhook with `national_id_match_score = 0.90` and verify it outputs `canonical_verification_pass = true`.
3. **Person B Flow:** Pass an FO payload with `VERIFIED_CLEAN` and verify it outputs `canonical_verification_pass = true`.
4. **Mixed Edge Cases:** Null `verified_income` for Person A must throw a 500 error at Normalization, preventing downstream formula execution.
5. **Failure Scenarios:** Verification status of `FRAUD_DETECTED` correctly outputs `false`, triggering a terminal reject in the Decision Table.
