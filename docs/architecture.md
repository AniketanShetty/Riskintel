# RiskIntel — System Architecture

**Version:** V1

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                  │
│                       (Vite + React)                                │
│                                                                     │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│   │ Person A Form│   │ Person B Form│   │ Employee Dashboard   │   │
│   └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘   │
└──────────┼──────────────────┼──────────────────────┼───────────────┘
           │                  │                      │
           ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                   │
│                     (Flask / FastAPI)                                │
│                                                                     │
│   POST /api/assess/person-a                                         │
│   POST /api/assess/person-b                                         │
│   POST /api/report/generate                                         │
│   GET  /api/report/download/{id}                                    │
└──────────┬──────────────────┬──────────────────────┬───────────────┘
           │                  │                      │
           ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ENGINE LAYER                                  │
│                                                                     │
│   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│   │ Eligibility      │  │ Readiness        │  │ PDF Report     │   │
│   │ Engine           │  │ Engine           │  │ Engine         │   │
│   │ (Dataset A)      │  │ (Dataset B)      │  │ (ReportLab)    │   │
│   └──────────────────┘  └──────────────────┘  └────────────────┘   │
│                                                                     │
│   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│   │ Risk Tier        │  │ Archetype        │  │ Recommendation │   │
│   │ Engine           │  │ Engine           │  │ Engine         │   │
│   │ (Dataset C)      │  │ (Dataset C)      │  │ (Dataset C)    │   │
│   └──────────────────┘  └──────────────────┘  └────────────────┘   │
└──────────┬──────────────────┬──────────────────────────────────────┘
           │                  │
           ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                    │
│                                                                     │
│   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│   │ data/raw/        │  │ data/processed/  │  │ models/        │   │
│   │ Source CSVs      │  │ Cleaned data     │  │ .joblib files  │   │
│   └──────────────────┘  └──────────────────┘  └────────────────┘   │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │ SQLite — assessments.db                                      │  │
│   │ Tables: assessments, reports                                 │  │
│   └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow — Person A

```
User Input
    │
    ▼
API: /api/assess/person-a
    │
    ├──▶ Eligibility Engine ──▶ Highly Likely / Likely / Borderline / Unlikely
    │         (Dataset A model)
    │
    ├──▶ Risk Tier Engine ──▶ P1 / P2 / P3 / P4
    │         (Dataset C model)
    │
    ├──▶ Archetype Engine ──▶ Stable / Credit-Seeking / Credit-Stressed / Established
    │         (Dataset C rules/clustering)
    │
    ├──▶ Recommendation Engine ──▶ Strengths + Risk Factors + Action Plan
    │         (Dataset C feature importance)
    │
    └──▶ Save to SQLite
              │
              ▼
         JSON Response → Frontend renders results
```

---

## Data Flow — Person B

```
User Input
    │
    ▼
API: /api/assess/person-b
    │
    ├──▶ Readiness Engine ──▶ Score (0–100) + Band
    │         (Dataset B model / scoring)
    │
    ├──▶ Livelihood Archetype Engine ──▶ Retail Micro-Business / Agri Entrepreneur / etc.
    │         (Dataset B rules/clustering)
    │
    ├──▶ Strengths + Weaknesses + Improvement Path
    │
    └──▶ Save to SQLite
              │
              ▼
         JSON Response → Frontend renders results
```

---

## Data Flow — Bank Employee Report

```
Assessment Record (from SQLite)
    │
    ▼
API: /api/report/generate
    │
    ├──▶ PDF Report Engine (ReportLab)
    │         Sections: Summary, Assessment, Signals, Actions, Notes
    │
    └──▶ Save PDF to reports/
              │
              ▼
         GET /api/report/download/{id} → PDF file
```

---

## Folder Responsibility Map

| Folder | Responsibility |
| :--- | :--- |
| `docs/` | Architecture, decisions, dataset docs, field specs, output specs |
| `docs/forms/` | Per-workflow input field definitions (Person A, Person B) |
| `docs/output_specs/` | Per-engine output schema definitions |
| `data/raw/` | Unmodified source datasets (CSV) |
| `data/processed/` | Cleaned, feature-engineered datasets |
| `models/` | Serialized trained models (.joblib) and scalers |
| `backend/` | API server, engine modules, data pipeline, PDF generator |
| `frontend/` | Vite + React client application |
| `reports/` | Generated PDF report files |
| `tests/` | Unit tests (engines), integration tests (API), validation tests |

---

## Engine Isolation Principle

Each engine is a self-contained module:

- Loads its own model artifact from `models/`
- Accepts a standardized input dict
- Returns a standardized output dict
- Has no dependency on other engines
- Can be tested independently

The API layer orchestrates engine calls and composes the final response.

---

## Naming Conventions

### Files

| Convention | Example |
| :--- | :--- |
| Python modules | `snake_case.py` — `eligibility_engine.py` |
| React components | `PascalCase.jsx` — `PersonAForm.jsx` |
| CSS files | `kebab-case.css` — `person-a-form.css` |
| Model artifacts | `{engine}_{version}.joblib` — `eligibility_v1.joblib` |
| Test files | `test_{module}.py` — `test_eligibility_engine.py` |

### API Endpoints

| Convention | Example |
| :--- | :--- |
| REST resource paths | `kebab-case` — `/api/assess/person-a` |
| Query parameters | `snake_case` — `?include_details=true` |

### Variables and Functions

| Convention | Example |
| :--- | :--- |
| Python | `snake_case` — `calculate_risk_tier()` |
| JavaScript | `camelCase` — `handleFormSubmit()` |
| React components | `PascalCase` — `<RiskTierBadge />` |
| Constants | `UPPER_SNAKE_CASE` — `MAX_CREDIT_SCORE` |
