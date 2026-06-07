# RiskIntel

**Loan Decision Support System — V1**

---

## Overview

RiskIntel is a backend-focused Loan Decision Support System designed with two equal, non-negotiable goals:
1. **Borrower-facing:** Provide transparent, fair loan assessments with plain-language explanations. Thin-file borrowers must receive an explicit, fair evaluation path rather than being silently rejected.
2. **Employee-facing:** Reduce manual arithmetic and subjective guesswork for loan officers by generating standardized, structured baseline reports. 

The final lending decision ALWAYS belongs to a human. RiskIntel is a heuristic decision-support tool, not an autonomous credit approval AI.

---

## What RiskIntel is NOT

- NOT a frontend project or UI showcase.
- NOT an autonomous lending AI.
- NOT an experimental ML playground.
- NOT a dashboard.

---

## Core Workflows (Minimum Viable RiskIntel)

### Person A — Credit-Aware Borrower
Applicants with a valid credit history and bureau score.
**Active Engine:**
- **E2 (Risk Tier Engine):** Deterministic policy engine mapping CIBIL scores to standard risk tiers (P1-P4).

*Note: E1 (Eligibility) is currently DISABLED pending data governance (see below).*

### Person B — Thin-File / New-To-Credit Borrower
Applicants with no credit history. They are explicitly routed to this path; silent rerouting is prohibited.
**Active Engines:**
- **E5 (Readiness Engine):** Deterministic heuristic scoring financial capacity without relying on bureau data.
- **E6 (Livelihood Engine):** Deterministic dictionary lookup mapping stated business types to standardized macro-categories.

---

## Current Audited Reality & Model Risk Status

Following a comprehensive Model Risk Committee audit, the repository is strictly governed by the following decisions:

| Component | Status | Reason |
| :--- | :--- | :--- |
| **E1 (Eligibility ML)** | **DISABLED** | The legacy model used synthetic data, lacked a commercial license, and output mathematically invalid probabilities. Must not be rebuilt until Data Governance procures a legally defensible dataset with proven lineage. |
| **E2 (Risk Tier)** | **KEEP** | Functioning as a deterministic policy engine. |
| **E3 (Archetype ML)** | **REMOVED** | Permanently removed due to broken clustering logic, fabricated labels, and restrictive data licensing. |
| **E5 (Readiness)** | **KEEP** | Functioning as the sole defensible V1 thin-file framework. A V2 redesign is proposed to remove poverty-correlated proxy variables (e.g., infrastructure penalties). |
| **E6 (Livelihood)** | **KEEP** | Functioning as a deterministic lookup. |

---

## Data Governance Blocker

**DATA GOVERNANCE IS THE PRIMARY BLOCKER FOR ANY NEW MODELING.**

Currently, zero production datasets in this repository possess a verified commercial use license or complete provenance. All legacy Kaggle, synthetic, and PII-exposed datasets have been explicitly removed or archived. 

*No machine learning model (e.g., Random Forest, KMeans) may be trained, tuned, or deployed until a real-world, legally procured dataset with a complete `provenance.json` is added to the repository.*

---

## Repository Structure

```text
riskintel/
├── README.md                        # Master Project Constitution
├── docs/                            # Governance and Policy Documentation
│   ├── THIN_FILE_POLICY.md
│   ├── THIN_FILE_EVALUATION_POLICY.md
│   ├── DATA_GOVERNANCE_PLAN.md
│   ├── DATASET_DECISIONS.md
│   ├── MODEL_RISK_COMMITTEE_DECISION.md
│   ├── E1_REPLACEMENT_STRATEGY.md
│   ├── LOAN_OFFICER_WORKFLOW_ANALYSIS.md
│   ├── MINIMUM_VIABLE_RISKINTEL.md
│   └── model_cards/                 # Documented policy logic for E2, E5, E6
│
├── archive/                         # Deprecated/Unlicensed data (Do not use)
│
├── backend/
│   ├── requirements.txt             # Pinned Python dependencies
│   ├── run.py                       # Application entry point
│   └── app/
│       ├── __init__.py              # Application factory
│       ├── orchestrator.py          # Primary entry point (E1 bypassed, E3 removed)
│       ├── routing.py               # Explicit Person A/B routing
│       └── engines/                 # E2, E5, E6 logic
│
└── tests/                           # Health and pipeline tests
```

---

## Quickstart

```bash
cd backend/

# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the API server
uvicorn app.main:app --reload
```

---

## Tech Stack & Architecture

- **Backend Framework:** FastAPI (Python >= 3.12)
- **Database:** SQLite via SQLAlchemy (async) and Alembic for migrations
- **Data Processing:** Pandas, NumPy
- **Testing:** Pytest, HTTPX, pytest-asyncio
- **PDF Reports:** ReportLab

---

## AI / Developer Onboarding Context

If you are an AI assistant or a new developer joining this project, read this carefully:
1. **Understand the Constraints:** Do NOT suggest adding autonomous ML models. We are strictly adhering to the Model Risk Committee's decision. E1 and E3 remain disabled/removed.
2. **Core Focus:** We only work with the deterministic engines (E2, E5, E6) and explicit routing for thin-file borrowers.
3. **Current Phase:** As per `MINIMUM_VIABLE_RISKINTEL.md`, we are in the **Data Governance and Documentation** phase. 
   - Immediate next tasks include: Documenting policy rationale for E2/E5 (Model Cards), generating `provenance.json`, consolidating a `LICENSE` inventory, and setting up CI/CD monitoring gates.
   - Do not attempt to rebuild E1 until a legally defensible dataset is available.

**Current Task for this Chat:** *(User: Replace this placeholder with your specific request for this chat, e.g., "Help me write the Model Card for E2", "Setup the CI/CD pipeline", or "Fix a bug in routing.py")*
