# RiskIntel V2: Deterministic Decision Table

This table maps every valid combination of the 8 core variables to exactly one of the 4 defined output states (`READY`, `NEARLY_READY`, `NOT_READY_YET`, `HARD_REJECT`). 

**Evaluation Rules:**
- The table evaluates top-to-bottom. 
- "Any" denotes that the variable's value does not change the outcome for that specific row.
- `available_capacity` evaluates the *total* capacity (Primary + Co-Applicant if present).
- `credit_score` evaluates the Primary Applicant (Co-Applicant trust failures are handled in ADR-021 as instant hard rejects, mapped here via the Co-Applicant's impact on the overall flow).

---

## 1. The Immutable Gates (Terminal Failures)
If an applicant hits any of these constraints, the system halts immediately. No optimization or co-applicant can override these states.

| `credit_score` | `active_dpd_days` | `bureau_settled_36m` | `verification_status` | `business_vintage_months` | `available_capacity` | `loan_purpose` | `coapplicant_present` | Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Any | **> 0** | Any | Any | Any | Any | Any | Any | **HARD_REJECT** |
| Any | Any | **True** | Any | Any | Any | Any | Any | **HARD_REJECT** |
| Any | Any | Any | **FRAUD_DETECTED** | Any | Any | Any | Any | **HARD_REJECT** |
| Any | Any | Any | **UNREACHABLE** | Any | Any | Any | Any | **HARD_REJECT** |
| Any | Any | Any | Any | **< 24** | Any | Any | Any | **HARD_REJECT** |
| Any | Any | Any | Any | Any | Any | **BANNED** | Any | **HARD_REJECT** |

---

## 2. The Affordability Mathematical Wall
If a borrower has zero or negative capacity for an indivisible asset, and a co-applicant has already been tried (or they have none but cannot be coached out of it), it hits a mathematical wall.

| `credit_score` | `active_dpd_days` | `bureau_settled_36m` | `verification_status` | `business_vintage_months` | `available_capacity` | `loan_purpose` | `coapplicant_present` | Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Any | 0 | False | CLEAN / VAR | >= 24 | **<= 0** | **INDIVISIBLE** | False | **NEARLY_READY** *(Requires Co-App)* |
| Any | 0 | False | CLEAN / VAR | >= 24 | **<= 0** | **INDIVISIBLE** | **True** | **NOT_READY_YET** |
| Any | 0 | False | CLEAN / VAR | >= 24 | **> 0 but < Target** | **INDIVISIBLE** | **True** | **NOT_READY_YET** |

---

## 3. The Trust Coaching Layer
If the primary applicant has a sub-prime bureau score (but no active defaults or write-offs), they are barred from `READY` unless a Co-Applicant is present.

| `credit_score` | `active_dpd_days` | `bureau_settled_36m` | `verification_status` | `business_vintage_months` | `available_capacity` | `loan_purpose` | `coapplicant_present` | Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **< 650** | 0 | False | CLEAN / VAR | >= 24 | >= Target | Valid | **False** | **NEARLY_READY** *(Requires Co-App)* |
| **< 650** | 0 | False | CLEAN / VAR | >= 24 | > 0 but < Target | DIVISIBLE | **False** | **NEARLY_READY** *(Requires Co-App)* |
| **< 650** | 0 | False | CLEAN / VAR | >= 24 | <= 0 | DIVISIBLE | **False** | **NEARLY_READY** *(Requires Co-App)* |
| **< 650** | 0 | False | CLEAN / VAR | >= 24 | >= Target | Valid | **True** | **READY** |

---

## 4. The Optimization Layer
For prime or verified thin-file borrowers, if the capacity is positive but insufficient, the Optimization Engine intervenes based on Divisibility.

| `credit_score` | `active_dpd_days` | `bureau_settled_36m` | `verification_status` | `business_vintage_months` | `available_capacity` | `loan_purpose` | `coapplicant_present` | Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| >= 650 or -1 | 0 | False | CLEAN / VAR | >= 24 | **> 0 but < Target** | **INDIVISIBLE** | **False** | **NEARLY_READY** *(Requires Co-App)* |
| >= 650 or -1 | 0 | False | CLEAN / VAR | >= 24 | **> 0 but < Target** | **DIVISIBLE** | **False** | **NEARLY_READY** *(Reduce Amount)* |
| >= 650 or -1 | 0 | False | CLEAN / VAR | >= 24 | **> 0 but < Target** | **DIVISIBLE** | **True** | **NEARLY_READY** *(Reduce Amount)* |
| >= 650 or -1 | 0 | False | CLEAN / VAR | >= 24 | **<= 0** | **DIVISIBLE** | **False** | **NEARLY_READY** *(Requires Co-App)* |
| >= 650 or -1 | 0 | False | CLEAN / VAR | >= 24 | **<= 0** | **DIVISIBLE** | **True** | **NOT_READY_YET** |

---

## 5. The Approval Layer
The absolute mathematical 'Happy Path' where all requirements are met and the borrower can sustain the requested loan.

| `credit_score` | `active_dpd_days` | `bureau_settled_36m` | `verification_status` | `business_vintage_months` | `available_capacity` | `loan_purpose` | `coapplicant_present` | Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **>= 650 or -1**| **0** | **False** | **CLEAN / VAR** | **>= 24** | **>= Target** | **DIVISIBLE** | **False** | **READY** |
| **>= 650 or -1**| **0** | **False** | **CLEAN / VAR** | **>= 24** | **>= Target** | **INDIVISIBLE**| **False** | **READY** |
| **Any (handled)** | **0** | **False** | **CLEAN / VAR** | **>= 24** | **>= Target** | **DIVISIBLE** | **True** | **READY** |
| **Any (handled)** | **0** | **False** | **CLEAN / VAR** | **>= 24** | **>= Target** | **INDIVISIBLE**| **True** | **READY** |
