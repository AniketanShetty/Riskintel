# BLOCKERS
*Items that prevent implementation.*

1. **Undefined Optimization Algebra:** `ADR-021` (Section 7.3) states the Engine "reduces the Loan Amount until target_emi == total_available_capacity" and "slides the Tenure lever to maximum." It is mathematically undefined whether the Engine immediately sets tenure to 60 or steps it monthly to find the minimum stretch. Furthermore, solving for reduced loan amount lacks the explicit Present Value (`PV`) formula. Two engineers will build completely different scaling loops (Algebraic inverse vs. Incremental loops).
2. **Missing Fuzzy Match Algorithm:** `SCORECARD_FORMULAS.md` (Section 4.2) dictates `national_id_match_score >= 0.85`. The exact algorithm (e.g., Levenshtein, Jaro-Winkler, Cosine Similarity) is undefined. Two engineers will use different libraries, destroying determinism.
3. **Undefined Pincode Multipliers:** `ADR-024` (Section 5) hardcodes Tier 1 = 1.8, but Tier 2, Tier 3, etc., are completely undefined in the documentation. Without the exact scalar values, `monthly_living_cost` cannot be calculated for non-Tier 1 applicants.
4. **Banned Loan Purposes:** `DECISION_TABLE.md` lists a `HARD_REJECT` condition where `loan_purpose == BANNED`. However, `ADR-024` explicitly lists only 7 permitted enum values. There is no mapping of what constitutes a "Banned" purpose or if anything outside the 7 is rejected at intake vs hitting the decision table.

# AMBIGUITIES
*Items requiring clarification.*

1. **PMT Compounding & Rounding:** `SCORECARD_FORMULAS.md` calls `PMT(interest_rate, loan_term, loan_amount)`. It does not define compounding frequency (is `SYSTEM_BASE_INTEREST_RATE` of 0.24 strictly `0.24/12` per period?) or whether the resulting EMI is rounded to the nearest integer. Floating point differences will break database determinism.
2. **Age Calculation Determinism:** `ADR-021` (Section 3) requires `age >= 18 AND age <= 70`. While `ADR-024` solved business vintage drift via month truncation, applicant age calculation is undefined. Using system clock `datetime.now()` breaks determinism if a payload is replayed; it must be bound to the session `created_at` timestamp or use explicit truncation.
3. **Account Aggregator Failure State:** `SCORECARD_FORMULAS.md` states Verification PASS requires `Account_Aggregator_Pull == SUCCESS`. If the AA pull fails (e.g., API timeout), the document does not explicitly define whether this throws a terminal `NOT_READY_YET` or allows a retry loop.
4. **Co-Applicant Baseline Assumption:** The reverse-algebra for `required_coapplicant_income_baseline` in `ADR-024` structurally assumes `co_app_existing_emi = 0`. If this is intentional, it must be explicitly declared as a known assumption; otherwise, the capacity prompt could be mathematically invalid.

# ASSUMPTIONS
*Items that appear implied but are not formally defined.*

1. **Zero Existing Debt:** Implied that if `existing_emi` is absent from Bureau/AA, it evaluates strictly as `0` in the PMT capacity math.
2. **Deterministic Time Anchor:** Implied that "Current_Year" and "Current_Month" in the `business_vintage_months` calculation (`ADR-024`) is anchored to the application submission date rather than the real-time execution clock to preserve determinism.
3. **Target EMI Margin:** `SCORECARD_FORMULAS.md` uses `emi_shortfall <= 0` implying that available capacity must merely match the target EMI with zero buffer/margin required.
4. **Co-Applicant Re-Verification Pipeline:** `ADR-025` normalizes Co-Applicant pathways, assuming that a Co-Applicant submitted via the Recovery Loop (`user_submits_coapplicant`) flows through the exact same physical/digital checks natively without requiring entirely new state transitions.

# IMPLEMENTATION-READY RULES
*Rules safe to implement immediately.*

1. **Livelihood Resilience (Rule R-03):** The `business_vintage_months >= 24` threshold and the explicit mathematical truncation equation `((Current_Year - issue_year) * 12) + (Current_Month - issue_month)`.
2. **Repayment Trust (Rule R-01 & R-05):** The CIBIL >= 650, active DPD == 0, and Settled == False boolean gates are mathematically un-ambiguous.
3. **Divisibility Routing:** The hard mapping of loan purposes to `DIVISIBLE` or `INDIVISIBLE` (`ADR-024`) and their exact consequences in the `DECISION_TABLE.md` paths.
4. **Tamper Evidence Cryptography:** The SHA-256 hash matching equations (`ADR-025`) are mathematically absolute.
5. **State Machine DAG:** The transition triggers, specifically the `NEARLY_READY` recovery hook and the `PENDING_REPROMPT` locks (`ADR-023`, `ADR-025`) are fully bounded.

# PHASE2 READINESS SCORE

**65/100**

*Explanation:* While the architecture, persistence integrity, and State Machine DAG are rock-solid, the core deterministic mandate fails at the optimization layer. Two engineers building the `Optimization Engine` and `Verification Processor` from this spec will produce mathematically divergent code due to missing algebraic steps for principal reduction, absent fuzzy matching algorithms, missing Pincode multiplier constants, and floating-point PMT rounding ambiguities. These blockers must be explicitly documented in ADRs before backend engineers touch the Python files.
