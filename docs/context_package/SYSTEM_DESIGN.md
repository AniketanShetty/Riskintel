# RiskIntel V2: System Design

## 1. Component Architecture
RiskIntel V2 is an acyclic pipeline (DAG) with two strictly defined cyclic recovery loops.

### 1.1 Ingestion & Triage Layer
*   **Responsibilities:** Parses categorical inputs (e.g., `"10k-20k"`) and calculates the absolute Best-Case scenario using the bracket's upper bound.
*   **Routing:** Automatically hard-rejects mathematically impossible requests before verification costs are incurred.

### 1.2 Canonical Normalization Layer (ADR-022)
*   **Responsibilities:** Solves the branch-merging failure between Digital (Person A) and Physical (Person B) pathways.
*   **Execution:** Converts source-specific variables (like `verified_monthly_cash_income` or `account_aggregator_salary_avg`) into unified `canonical_` variables.

### 1.3 Cryptographic Tamper Layer (ADR-025)
*   **Responsibilities:** Enforces the Constitution's mandate for tamper-evident physical assessments.
*   **Execution:** Computes `tamper_evidence_pass` by checking `SHA256(received)` against the webhook `hash`.

### 1.4 Core Optimization Engine
*   **Responsibilities:** Executes `PMT` algorithms, date-diff functions, and capacity calculations.
*   **Levers:** Stretches Tenure up to `SYSTEM_MAX_TENURE`. Reduces Amount down to `SYSTEM_MIN_LOAN_AMOUNT` (only if the product is `DIVISIBLE`). Reverse-engineers the `required_coapplicant_income_baseline`.

### 1.5 Decision Table & State Machine
*   **Responsibilities:** Converts boolean math results into exact DAG states.
*   **Execution:** Evaluates constraints like `livelihood_resilience_pass`, `co_app_canonical_verification_pass`, and Divisibility to issue `READY`, `NEARLY_READY`, or `NOT_READY_YET`.
