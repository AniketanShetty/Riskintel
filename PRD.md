# RiskIntel — Product Requirements Document

**Version:** V1

---

## Product Vision

RiskIntel is a Loan Decision Support System that helps:

1. **Applicants** understand their loan readiness and risk profile.
2. **Bank employees** reduce manual underwriting effort.

The system explains outcomes and provides actionable recommendations rather than simply returning an approval decision.

---

## Target Users

### User Type A — Credit-Aware Borrower

| Attribute | Detail |
| :--- | :--- |
| Credit History | Existing |
| Credit Score | Available (300–900) |
| Banking Activity | Previous formal borrowing |

### User Type B — New-To-Credit (NTC) Borrower

| Attribute | Detail |
| :--- | :--- |
| Credit History | None or minimal |
| Credit Score | Not available or unreliable |
| Borrowing History | Limited formal history |

### Bank Employee

| Attribute | Detail |
| :--- | :--- |
| Role | Reviews applications |
| Task | Performs underwriting checks |
| Need | Concise decision-support information |

---

## Functional Requirements

### Person A Workflow

#### Inputs

- Income
- Loan Amount
- Loan Purpose
- Assets
- Credit Score
- Credit History Features
- Education
- Employment Status
- Dependents
- Marital Status
- Property Area

#### Outputs

**Eligibility Assessment**

| Value | Meaning |
| :--- | :--- |
| Highly Likely | Strong approval indicators |
| Likely | Good approval indicators |
| Borderline | Mixed signals |
| Unlikely | Weak approval indicators |

**Risk Tier**

| Tier | User-Friendly Label |
| :--- | :--- |
| P1 | Low Risk |
| P2 | Moderate Risk |
| P3 | Elevated Risk |
| P4 | High Risk |

**Borrower Archetype**

Examples:

- Stable Borrower
- Credit-Seeking Borrower
- Credit-Stressed Borrower
- Established Borrower

**Strengths** — Top positive factors.

**Risk Factors** — Top risk factors.

**Action Plan** — Personalized recommendations.

---

### Person B Workflow

#### Inputs

- Income
- Expenses
- Loan Amount
- Loan Purpose
- Business Type
- Dependents
- Housing Information
- Infrastructure Information
- Business Duration

#### Outputs

**Readiness Score**

Range: 0–100

**Readiness Band**

| Band | Meaning |
| :--- | :--- |
| Ready | Strong readiness indicators |
| Moderately Ready | Adequate with some gaps |
| Needs Improvement | Significant gaps present |
| High Risk | Major concerns identified |

**Livelihood Archetype**

Examples:

- Retail Micro-Business
- Agri Entrepreneur
- Home-Based Producer

**Strengths** — Top positive factors.

**Weaknesses** — Top risk factors.

**Improvement Path** — Personalized next steps.

> **Important:** No approval probability is shown for Person B.

---

### Bank Employee Workflow

Generate a downloadable PDF report.

**Sections:**

1. Applicant Summary
2. Assessment Summary
3. Positive Signals
4. Risk Signals
5. Recommended Review Actions
6. Supporting Notes

---

## Dataset Mapping

| Dataset | Purpose |
| :--- | :--- |
| Dataset A — Loan Approval Prediction | Eligibility Assessment |
| Dataset B — RuralCreditData | Person B Readiness Engine |
| Dataset C — Leading Indian Bank + CIBIL | Risk Tier Engine · Borrower Archetype Engine · Recommendation Engine |

---

## Constraints

### Accepted Limitation 1

`Approved_Flag` is highly correlated with Credit Score.

Risk Tier should be treated as a policy/risk-grade signal, not a true default-risk outcome.

### Accepted Limitation 2

Person B does not have approval labels.

Therefore: **Readiness ≠ Approval Probability**

### Accepted Limitation 3

Recommendations are advisory and educational.

**Not financial advice.**

---

## Success Criteria

**Applicant should understand:**

- Current status
- Key strengths
- Key weaknesses
- Recommended next actions

**Bank employee should be able to review the generated report faster than manual review.**

---

## Out of Scope (V1)

- Deep Learning
- LLM Decision Making
- Real-Time Bureau Integration
- Dynamic Recommendation Generation
- Regulatory Adverse Action Notices
- Additional Datasets

---

## Development Priority

| Phase | Deliverable |
| :--- | :--- |
| Phase 1 | Forms — Input field specifications |
| Phase 2 | Data Processing Pipeline |
| Phase 3 | Eligibility Engine |
| Phase 4 | Risk Tier Engine |
| Phase 5 | Archetype Engine |
| Phase 6 | Recommendation Engine |
| Phase 7 | PDF Report Generation |
| Phase 8 | Frontend Integration |
