# JUDGE ATTACK MATRIX V2 (Acceptance Criteria)

This document maps the `CREDIT_POLICY_V2` guardrails into 100 deterministic test scenarios. It serves as the definitive acceptance criteria for the V2 Orchestrator implementation.

## Part 1: Person A (Credit-Aware Pipeline)

| Scenario ID | Inputs (Age, Term, Income, Loan, CIBIL) | Expected Outcome | Expected Override Flags | Expected Explanation | Why the scenario exists |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A-NORM-01** | Age=30, Term=20, Inc=1.2M, Loan=3M, CIBIL=820 | Likely | *None* | A-STR-001 (P1 Credit) | Baseline prime salaried borrower |
| **A-NORM-02** | Age=45, Term=10, Inc=800k, Loan=1.5M, CIBIL=740 | Likely | *None* | A-STR-002 (Good Credit) | Baseline mid-market borrower |
| **A-NORM-03** | Age=25, Term=5, Inc=500k, Loan=500k, CIBIL=680 | Likely | *None* | A-STR-001 (P3 Acceptable) | Baseline entry-level borrower |
| **A-NORM-04** | Age=50, Term=15, Inc=2.5M, Loan=8M, CIBIL=780 | Likely | *None* | A-STR-001 | High-net-worth normal |
| **A-NORM-05** | Age=35, Term=12, Inc=600k, Loan=2.5M, CIBIL=660 | Unlikely | *None* | A-RISK-002 (Low Score) | Normal rejection via ML probabilities |
| **A-LTI-01** | Age=30, Term=20, Inc=1M, Loan=5.9M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: LTI exactly 5.9x (Passes) |
| **A-LTI-02** | Age=30, Term=20, Inc=1M, Loan=6M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: LTI exactly 6.0x (Passes) |
| **A-LTI-03** | Age=30, Term=20, Inc=1M, Loan=6.1M, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 (LTI Limit) | Edge Case: LTI exactly 6.1x (Trips guardrail) |
| **A-LTI-04** | Age=30, Term=20, Inc=500k, Loan=5M, CIBIL=850 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Adversarial: Perfect CIBIL masking 10x LTI |
| **A-LTI-05** | Age=30, Term=20, Inc=100k, Loan=50M, CIBIL=850 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Judge Attack: 500x LTI |
| **A-LTI-06** | Age=30, Term=20, Inc=0, Loan=1M, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Judge Attack: Zero income, Division by Zero safety |
| **A-LTI-07** | Age=30, Term=20, Inc=-50k, Loan=1M, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Judge Attack: Negative income evasion |
| **A-LTI-08** | Age=30, Term=20, Inc=1M, Loan=100M, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Judge Attack: Extreme principal request |
| **A-LTI-09** | Age=30, Term=20, Inc=10k, Loan=200k, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Micro-fraud: 20x LTI on tiny nominal sums |
| **A-LTI-10** | Age=30, Term=20, Inc=1, Loan=1M, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION` | A-POLICY-003 | Judge Attack: 1 INR income |
| **A-AGE-01** | Age=49, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: Maturity Age = 69 (Passes) |
| **A-AGE-02** | Age=50, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: Maturity Age = 70 (Passes) |
| **A-AGE-03** | Age=51, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_AGE_TERM_REJECTION` | A-POLICY-002 (Age Limit) | Edge Case: Maturity Age = 71 (Trips guardrail) |
| **A-AGE-04** | Age=65, Term=10, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_AGE_TERM_REJECTION` | A-POLICY-002 | Banking Reality: 75 year maturity |
| **A-AGE-05** | Age=70, Term=2, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_AGE_TERM_REJECTION` | A-POLICY-002 | Banking Reality: 72 year maturity |
| **A-AGE-06** | Age=150, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_AGE_TERM_REJECTION` | A-POLICY-002 | Judge Attack: The Immortal Borrower |
| **A-AGE-07** | Age=900, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_AGE_TERM_REJECTION` | A-POLICY-002 | Judge Attack: The Vampire Borrower |
| **A-AGE-08** | Age=69, Term=2, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_AGE_TERM_REJECTION` | A-POLICY-002 | Edge Case: Maturity = 71 |
| **A-AGE-09** | Age=68, Term=2, Inc=1M, Loan=2M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: Maturity = 70 |
| **A-AGE-10** | Age=12, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `OVERRIDE_MIN_AGE` | A-POLICY-005 (Min Age) | Judge Attack: Child Borrower (Age < 18) |
| **A-INC-01** | Age=30, Term=20, Inc=301k, Loan=1M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: Income exactly above subsistence |
| **A-INC-02** | Age=30, Term=20, Inc=300k, Loan=1M, CIBIL=800 | Likely | *None* | A-STR-001 | Edge Case: Income exactly at subsistence |
| **A-INC-03** | Age=30, Term=20, Inc=299k, Loan=1M, CIBIL=800 | Likely | `FLAG_LOW_INCOME_REVIEW` | A-STR-001 (+ Warning) | Edge Case: Income below subsistence (Review required) |
| **A-INC-04** | Age=30, Term=20, Inc=150k, Loan=500k, CIBIL=800 | Likely | `FLAG_LOW_INCOME_REVIEW` | A-STR-001 (+ Warning) | Banking Reality: True poverty line micro-loan |
| **A-INC-05** | Age=30, Term=20, Inc=10k, Loan=30k, CIBIL=800 | Likely | `FLAG_LOW_INCOME_REVIEW` | A-STR-001 (+ Warning) | Judge Attack: Ultra-low principal and income |
| **A-INC-06** | Age=30, Term=20, Inc=0, Loan=100k, CIBIL=800 | Unlikely | `OVERRIDE_LTI_REJECTION`, `FLAG_LOW_INCOME` | A-POLICY-003 | Adversarial overlap: 0 income triggers both |
| **A-INC-07** | Age=30, Term=20, Inc=200k, Loan=1M, CIBIL=500 | Unlikely | `OVERRIDE_E2_P4`, `FLAG_LOW_INC` | A-POLICY-001 | Reality: Destitute + terrible credit |
| **A-INC-08** | Age=30, Term=20, Inc=250k, Loan=500k, CIBIL=700 | Likely | `FLAG_LOW_INCOME_REVIEW` | A-STR-002 (+ Warning) | Normal microfinance applicant |
| **A-INC-09** | Age=30, Term=20, Inc=299,999, Loan=1M, CIBIL=800| Likely | `FLAG_LOW_INCOME_REVIEW` | A-STR-001 (+ Warning) | Precision check |
| **A-INC-10** | Age=30, Term=20, Inc=-1, Loan=1M, CIBIL=800 | Unlikely | `OVERRIDE_LTI`, `FLAG_LOW_INC` | A-POLICY-003 | Negative income fallback |
| **A-P4-01** | Age=30, Term=20, Inc=1M, Loan=2M, CIBIL=400 | Unlikely | `OVERRIDE_E2_P4_REJECTION` | A-POLICY-001 (Credit) | V1 Regression: ML says Likely, E2 overrides to Unlikely |
| **A-P4-02** | Age=30, Term=20, Inc=10M, Loan=1M, CIBIL=300 | Unlikely | `OVERRIDE_E2_P4_REJECTION` | A-POLICY-001 | Adversarial: Massive income masked terrible credit |
| **A-P4-03** | Age=30, Term=20, Inc=1M, Loan=2M, CIBIL=450 | Unlikely | *None* | A-RISK-002 | V1 Regression: ML naturally says Unlikely |
| **A-P4-04** | Age=30, Term=20, Inc=5M, Loan=1M, CIBIL=0 | Unlikely | `OVERRIDE_E2_P4_REJECTION` | A-POLICY-001 | Edge Case: CIBIL is mathematically 0 |
| **A-P4-05** | Age=30, Term=20, Inc=1M, Loan=2M, CIBIL=-1 | Unlikely | `OVERRIDE_E2_P4_REJECTION` | A-POLICY-001 | Edge Case: Negative CIBIL |
| **A-CMB-01** | Age=80, Term=20, Inc=100k, Loan=50M, CIBIL=300 | Unlikely | `AGE`, `LTI`, `P4`, `LOW_INC` | A-POLICY-002 (Age) | The "Everything Everywhere All At Once" Attack |
| **A-CMB-02** | Age=80, Term=20, Inc=100k, Loan=50M, CIBIL=800 | Unlikely | `AGE`, `LTI`, `LOW_INC` | A-POLICY-002 (Age) | Age > LTI in precedence sorting |
| **A-CMB-03** | Age=30, Term=20, Inc=100k, Loan=50M, CIBIL=300 | Unlikely | `LTI`, `P4`, `LOW_INC` | A-POLICY-001 (Credit) | P4 > LTI in precedence sorting |
| **A-CMB-04** | Age=60, Term=20, Inc=100k, Loan=500k, CIBIL=800 | Unlikely | `AGE`, `LOW_INC` | A-POLICY-002 (Age) | Age override with review flag |
| **A-CMB-05** | Age=30, Term=20, Inc=500k, Loan=50M, CIBIL=800 | Unlikely | `LTI` | A-POLICY-003 (LTI) | Pure LTI failure |
| **A-CMB-06** | Age=30, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Likely | *None* | A-STR-001 | Control scenario |
| **A-CMB-07** | Age=40, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Likely | *None* | A-STR-001 | Control scenario |
| **A-CMB-08** | Age=70, Term=1, Inc=1M, Loan=2M, CIBIL=800 | Unlikely | `AGE` | A-POLICY-002 | Edge case overlapping term |
| **A-CMB-09** | Age=69, Term=1, Inc=1M, Loan=10M, CIBIL=800 | Unlikely | `LTI` | A-POLICY-003 | Passes age, fails LTI |
| **A-CMB-10** | Age=18, Term=20, Inc=1M, Loan=2M, CIBIL=800 | Likely | *None* | A-STR-001 | Legal adult baseline |


## Part 2: Person B (New-To-Credit Pipeline)

| Scenario ID | Inputs (Financial, Business, Loan_Income_Ratio, Purpose) | Expected Outcome | Expected Override Flags | Expected Explanation | Why the scenario exists |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B-NORM-01** | Fin=80, Biz=80, LIR=0.5, Purpose=Aligned | Ready | *None* | Strong Readiness | Baseline NTC success |
| **B-NORM-02** | Fin=60, Biz=60, LIR=1.0, Purpose=Neutral | Moderately Ready | *None* | Average Readiness | Baseline mid-market NTC |
| **B-NORM-03** | Fin=30, Biz=30, LIR=1.4, Purpose=Misaligned | Needs Improvement | *None* | Weak Readiness | Baseline weak NTC |
| **B-NORM-04** | Fin=90, Biz=90, LIR=0.1, Purpose=Aligned | Ready | *None* | Excellent Readiness | High-potential NTC |
| **B-NORM-05** | Fin=0.6, Biz=50, LIR=1.0, Purpose=Neutral | Not Ready | *None* | V1 Regression | ML naturally outputs Not Ready (Fin barely passes floor) |
| **B-FLR-01** | Fin=0.49, Biz=100, House=100, LIR=1.0, Pur=Aligned | Not Ready | `OVERRIDE_E5_FLOOR_BREACH` | Financial Floor Rejection | V1 Regression: Fin < 0.5 triggers override |
| **B-FLR-02** | Fin=0.50, Biz=100, House=100, LIR=1.0, Pur=Aligned | Moderately Ready | *None* | Score Compression Masking | Edge Case: Fin exactly 0.5 passes V1 floor |
| **B-FLR-03** | Fin=39.9, Biz=100, House=100, LIR=1.0, Pur=Aligned | Needs Improvement | `OVERRIDE_SUB_SCORE_FLOOR` | Component Floor Rejection | V2 Guardrail: Component < 40 limits total band |
| **B-FLR-04** | Fin=40.0, Biz=100, House=100, LIR=1.0, Pur=Aligned | Moderately Ready | *None* | Moderate Readiness | Edge Case: Component exactly 40 passes gate |
| **B-FLR-05** | Fin=100, Biz=39.9, House=100, LIR=1.0, Pur=Aligned | Needs Improvement | `OVERRIDE_SUB_SCORE_FLOOR` | Component Floor Rejection | V2 Guardrail: Business viability < 40 |
| **B-FLR-06** | Fin=0, Biz=100, House=100, LIR=1.0, Pur=Aligned | Not Ready | `OVERRIDE_E5_FLOOR_BREACH` | Financial Floor Rejection | Absolute 0 financial health |
| **B-FLR-07** | Fin=100, Biz=0, House=100, LIR=1.0, Pur=Aligned | Needs Improvement | `OVERRIDE_SUB_SCORE_FLOOR` | Component Floor Rejection | Absolute 0 business viability |
| **B-FLR-08** | Fin=39.9, Biz=39.9, House=100, LIR=1.0, Pur=Aligned | Needs Improvement | `OVERRIDE_SUB_SCORE_FLOOR` | Component Floor Rejection | Multiple failing components |
| **B-FLR-09** | Fin=100, Biz=100, House=0, LIR=1.0, Pur=Aligned | Ready | *None* | Strong Readiness | House=0 is not a component floor block |
| **B-FLR-10** | Fin=40, Biz=40, House=100, LIR=1.0, Pur=Aligned | Moderately Ready | *None* | Average Readiness | Passes component floors precisely |
| **B-DBT-01** | Fin=100, Biz=100, LIR=2.9, Pur=Aligned | Ready | *None* | Strong Readiness | Edge Case: Debt exactly at 2.9 (Passes) |
| **B-DBT-02** | Fin=100, Biz=100, LIR=3.0, Pur=Aligned | Ready | *None* | Strong Readiness | Edge Case: Debt exactly at 3.0 (Passes) |
| **B-DBT-03** | Fin=100, Biz=100, LIR=3.1, Pur=Aligned | Not Ready | `EXTREME_DEBT_FLOOR`, `E5_FLOOR` | Financial Floor Rejection | V2 Guardrail: LIR > 3.0 zeroes out Financial health |
| **B-DBT-04** | Fin=100, Biz=100, LIR=100.0, Pur=Aligned | Not Ready | `EXTREME_DEBT_FLOOR`, `E5_FLOOR` | Financial Floor Rejection | Judge Attack: Massive leverage request |
| **B-DBT-05** | Fin=100, Biz=100, LIR=1000.0, Pur=Aligned | Not Ready | `EXTREME_DEBT_FLOOR`, `E5_FLOOR` | Financial Floor Rejection | Judge Attack: Astronomical leverage |
| **B-DBT-06** | Fin=100, Biz=100, LIR=Infinity, Pur=Aligned | Not Ready | `EXTREME_DEBT_FLOOR`, `E5_FLOOR` | Financial Floor Rejection | Judge Attack: Div by Zero leverage mapping |
| **B-DBT-07** | Fin=40, Biz=100, LIR=3.1, Pur=Aligned | Not Ready | `EXTREME_DEBT_FLOOR`, `E5_FLOOR` | Financial Floor Rejection | Marginal fin health zeroed by leverage |
| **B-DBT-08** | Fin=100, Biz=100, LIR=0.0, Pur=Aligned | Ready | *None* | Strong Readiness | Zero leverage |
| **B-DBT-09** | Fin=100, Biz=100, LIR=-1.0, Pur=Aligned | Not Ready | `EXTREME_DEBT_FLOOR` | Financial Floor Rejection | Judge Attack: Negative leverage evaluation |
| **B-DBT-10** | Fin=100, Biz=100, LIR=2.999, Pur=Aligned | Ready | *None* | Strong Readiness | Precision logic check |
| **B-PUR-01** | Fin=100, Biz=100, LIR=1.0, Biz=Agri, Pur=Agri | Ready | *None* | Strong Readiness | Baseline aligned purpose |
| **B-PUR-02** | Fin=100, Biz=100, LIR=1.0, Biz=Retail, Pur=Biz | Ready | *None* | Strong Readiness | Baseline aligned purpose |
| **B-PUR-03** | Fin=100, Biz=100, LIR=1.0, Biz=Agri, Pur=Biz | Ready | `FLAG_PURPOSE_MISMATCH` | Strong Readiness (+ Warning) | V2 Guardrail: Review flag for Agriculture applying for Business loan |
| **B-PUR-04** | Fin=100, Biz=100, LIR=1.0, Biz=Retail, Pur=Agri | Ready | `FLAG_PURPOSE_MISMATCH` | Strong Readiness (+ Warning) | V2 Guardrail: Review flag for Retail applying for Ag loan |
| **B-PUR-05** | Fin=100, Biz=100, LIR=1.0, Biz=Prod, Pur=Agri | Ready | `FLAG_PURPOSE_MISMATCH` | Strong Readiness (+ Warning) | V2 Guardrail: Production mismatch |
| **B-PUR-06** | Fin=100, Biz=100, LIR=1.0, Biz=Serv, Pur=Agri | Ready | `FLAG_PURPOSE_MISMATCH` | Strong Readiness (+ Warning) | V2 Guardrail: Services mismatch |
| **B-PUR-07** | Fin=39.9, Biz=100, LIR=1.0, Biz=Agri, Pur=Biz | Needs Improvement | `SUB_SCORE`, `PURPOSE_MISMATCH` | Component Floor Rejection | Mismatch combined with component floor |
| **B-PUR-08** | Fin=100, Biz=100, LIR=1.0, Biz=Null, Pur=Null | Ready | *None* | Strong Readiness | Missing purpose data fallback |
| **B-PUR-09** | Fin=100, Biz=100, LIR=1.0, Biz=Agri, Pur=Null | Ready | *None* | Strong Readiness | Missing purpose mapped to Personal |
| **B-PUR-10** | Fin=100, Biz=100, LIR=3.1, Biz=Agri, Pur=Biz | Not Ready | `EXTREME_DEBT`, `E5_FLOOR`, `MISMATCH`| Financial Floor Rejection | Massive leverage with purpose fraud |
| **B-CMB-01** | Fin=0, Biz=0, LIR=100.0, Pur=Misaligned | Not Ready | `E5`, `DEBT`, `SUB`, `MISMATCH` | Financial Floor Rejection | The "Everything" Attack |
| **B-CMB-02** | Fin=100, Biz=39.9, LIR=3.1, Pur=Aligned | Not Ready | `E5`, `DEBT`, `SUB` | Financial Floor Rejection | Extreme debt overrides business weakness |
| **B-CMB-03** | Fin=39.9, Biz=100, LIR=1.0, Pur=Misaligned | Needs Improvement | `SUB`, `MISMATCH` | Component Floor Rejection | Component limit + Mismatch |
| **B-CMB-04** | Fin=50, Biz=50, LIR=1.0, Pur=Aligned | Moderately Ready | *None* | Average Readiness | Control |
| **B-CMB-05** | Fin=40, Biz=40, LIR=3.0, Pur=Aligned | Moderately Ready | *None* | Average Readiness | Edge case control |
| **B-CMB-06** | Fin=39.9, Biz=39.9, LIR=3.1, Pur=Misaligned | Not Ready | `DEBT`, `E5`, `SUB`, `MISMATCH` | Financial Floor Rejection | Fails everywhere |
| **B-CMB-07** | Fin=100, Biz=100, LIR=1.0, Pur=Aligned, Dep=0 | Ready | *None* | Strong Readiness | 0 Dependents |
| **B-CMB-08** | Fin=100, Biz=100, LIR=1.0, Pur=Aligned, Dep=50 | Moderately Ready | *None* | Household Burden | Judge Attack: 50 dependents reduces score but no hard override |
| **B-CMB-09** | Fin=100, Biz=100, LIR=1.0, Pur=Aligned, Dep=-5 | Ready | *None* | Strong Readiness | Judge Attack: Negative dependents clamped |
| **B-CMB-10** | Fin=100, Biz=100, LIR=1.0, Pur=Aligned, Age=10 | Ready | `OVERRIDE_MIN_AGE` | Min Age Policy | Judge Attack: Child borrower NTC |
| **B-CMB-11** | Fin=100, Biz=100, LIR=1.0, Pur=Aligned, Age=99 | Ready | `OVERRIDE_AGE_TERM_REJECTION` | Age Limit Policy | Judge Attack: Elderly borrower NTC |
| **B-CMB-12** | Fin=0.5, Biz=40, LIR=2.9, Pur=Neutral | Moderately Ready | *None* | Average Readiness | Exact threshold survivor |
| **B-CMB-13** | Fin=0.49, Biz=39.9, LIR=3.0, Pur=Misaligned | Not Ready | `E5_FLOOR`, `SUB`, `MISMATCH` | Financial Floor Rejection | Fails multiple tight edges |
| **B-CMB-14** | Fin=75, Biz=75, LIR=1.0, Pur=Aligned | Ready | *None* | Strong Readiness | Solid pass |
| **B-CMB-15** | Fin=100, Biz=100, LIR=1.5, Pur=Aligned | Ready | *None* | Strong Readiness | Exactly at debt burden dropoff limit |
