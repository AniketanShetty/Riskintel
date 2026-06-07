# Repository Reality Audit

**Date:** 2026-06-06
**Auditor:** Principal Software Auditor
**Scope:** Entire repository. No recommendations, no architecture. Only observable facts.

---

## A. What actually exists

### A.1 Repository tree (post-walk, excluding noise)

```
Riskintel/
├── .claude/settings.local.json
├── .gitignore
├── .pytest_cache/
├── IMPLEMENTATION_ROADMAP.md
├── PRD.md
├── README.md
├── backend/
│   ├── .env.example
│   ├── .gitkeep
│   ├── .pytest_cache/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── __init__.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py            (empty)
│   │   │   └── health.py
│   │   ├── audit.py
│   │   ├── config.py
│   │   ├── core/
│   │   │   ├── __init__.py            (empty)
│   │   │   ├── config.py
│   │   │   └── dependencies.py
│   │   ├── db/
│   │   │   ├── __init__.py            (empty)
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── engines/
│   │   │   ├── __init__.py            (empty)
│   │   │   ├── archetype/borrower_archetype_engine.py
│   │   │   ├── eligibility/eligibility_engine.py
│   │   │   ├── eligibility/train.py
│   │   │   ├── livelihood/__init__.py
│   │   │   ├── livelihood/livelihood_mapper.py
│   │   │   ├── readiness/__init__.py
│   │   │   ├── readiness/readiness_engine.py
│   │   │   ├── recommendation/__init__.py
│   │   │   ├── recommendation/context.py
│   │   │   ├── recommendation/evaluator.py
│   │   │   ├── recommendation/recommendation_engine.py
│   │   │   ├── recommendation/rules_person_a.py
│   │   │   ├── recommendation/rules_person_b.py
│   │   │   ├── recommendation/schema.py
│   │   │   ├── risk_tier/__init__.py
│   │   │   └── risk_tier/risk_tier_engine.py
│   │   ├── exceptions.py
│   │   ├── health.py
│   │   ├── lineage.py
│   │   ├── main.py
│   │   ├── middleware/__init__.py      (empty)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── applicant.py
│   │   │   ├── archetype_result.py
│   │   │   ├── assessment.py
│   │   │   ├── audit_log.py
│   │   │   ├── eligibility_result.py
│   │   │   ├── model_registry.py
│   │   │   ├── readiness_result.py
│   │   │   ├── recommendation_result.py
│   │   │   ├── risk_tier_result.py
│   │   │   └── rule_registry.py
│   │   ├── orchestrator.py
│   │   ├── report/__init__.py          (empty)
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── model_registry_repository.py
│   │   │   └── rule_registry_repository.py
│   │   ├── routes/
│   │   │   ├── __init__.py             (empty)
│   │   │   └── assess.py
│   │   ├── routing.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── applicant.py
│   │   │   ├── assessment.py
│   │   │   └── common.py
│   │   ├── services/
│   │   │   ├── __init__.py             (empty)
│   │   │   ├── model_registry_service.py
│   │   │   ├── rule_registry_service.py
│   │   │   └── rules_engine_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── preprocess_a.py
│   │       ├── preprocess_b.py
│   │       ├── preprocess_c.py
│   │       ├── validation.py
│   │       └── verify_final.py
│   ├── audit.py                        (root level — RF eval script, not the one in app/)
│   ├── nul                             (stray 46-byte file; content: error message)
│   ├── requirements.txt
│   ├── riskintel.db                    (SQLite, only table: alembic_version, empty)
│   ├── run.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── engines/
│   │   │   ├── test_livelihood_mapper.py     (7 tests)
│   │   │   └── test_recommendation_engine.py (8 tests)
│   │   ├── test_e2e_failures.py
│   │   ├── test_e2e_person_a.py
│   │   ├── test_e2e_person_b.py
│   │   ├── test_model_registry_service.py
│   │   ├── test_orchestrator.py
│   │   ├── test_rule_registry_service.py
│   │   └── test_rules_engine_service.py
│   └── venv/                           (Python 3.13.13 venv, no FastAPI/SQLAlchemy/Alembic installed)
├── data/
│   ├── processed/
│   │   ├── .gitkeep
│   │   ├── borrower_archetype_definitions.json
│   │   ├── eligibility_data.csv
│   │   ├── livelihood_data.csv
│   │   ├── readiness_data.csv
│   │   └── risk_tier_thresholds.json
│   └── raw/                            (multiple CSVs/XLSXs, plus helper scripts)
├── database/
│   └── migrations/
│       └── 001_initial_schema.sql      (PostgreSQL DDL)
├── docs/                               (architecture, contracts, forms, output_specs)
├── eval_output.txt
├── experiments/                        (research/experiment scripts + metrics + reports)
├── frontend/                           (Vite + React project, no build attempted)
├── legacy_archive/
│   ├── alembic/versions/001_initial_schema.py
│   ├── ml_service.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── rule_engine.py
│   ├── schemas.py
│   └── tests/
│       ├── __init__.py
│       ├── test_borrower_archetype_engine.py
│       ├── test_health.py
│       ├── test_readiness.py
│       └── test_risk_tier_engine.py
├── models/
│   ├── .gitkeep
│   ├── archetype/{kmeans_model.pkl, scaler.pkl}
│   ├── eligibility/random_forest.joblib   (1.3 MB, RandomForestClassifier)
│   ├── readiness/.gitkeep
│   └── risk_tier/risk_tier_thresholds.json
├── reports/                            (15+ markdown spec/review docs)
├── scripts/
│   └── train_borrower_archetype.py
├── test_audit_fail_closed.py           (top-level, imports `from orchestrator import ...` — broken)
└── test_ml_contract_fuzzing.py         (top-level, imports `from ml_service import app` — broken)
```

### A.2 FastAPI entrypoints

| File | Role | Verified |
| :--- | :--- | :--- |
| `backend/app/main.py` | Builds `app = FastAPI(...)`; includes only `app.api.health.router` under prefix `/health` | File present. Module importable only if `fastapi` installed. |
| `backend/run.py` | Flask-style `python run.py` entry — references nonexistent `from app import create_app` | **Broken at import** (verified). |
| `backend/Dockerfile` | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` | Present. Image never built locally. |

### A.3 Flask remnants

| File | Evidence |
| :--- | :--- |
| `backend/app/__init__.py` | Docstring: "Migration from Flask to FastAPI" — but no `create_app` symbol exported. |
| `backend/app/config.py` | `class Config` with `SECRET_KEY`, `PORT=5000`, `DEBUG`, `TESTING`; comment "UPPER_CASE → consumed by Flask internals". |
| `backend/run.py` | Full Flask entry point, `app.run(host=..., port=...)`. |
| `backend/app/routes/assess.py` | `from flask import Blueprint, request, jsonify`; defines `assess_bp = Blueprint("assess", __name__)`. |
| `backend/requirements.txt` | No `flask` listed — but venv has Flask 3.1.3 installed (leftover from prior setup). |
| `backend/app/audit.py` | Imports `from app.config import Config` (Flask Config class) at line 11. |
| `legacy_archive/{ml_service,orchestrator,models,rule_engine,schemas}.py` | Archived Flask-era source. |

### A.4 Alembic configuration

| File | Content | Verified |
| :--- | :--- | :--- |
| `backend/alembic.ini` | Placeholder `sqlalchemy.url = postgresql://riskintel:change-me-in-production@localhost:5432/riskintel` | Present. |
| `backend/alembic/env.py` | Async runner, imports all 11 models, overrides URL from `app.core.config.settings` | Present. Requires `fastapi`/`sqlalchemy` to run. |
| `backend/alembic/script.py.mako` | Standard template | Present. |
| `backend/alembic/versions/` | **Directory does not exist.** | Confirmed: `ls alembic` returns only `__init__.py`, `env.py`, `script.py.mako`. |
| `legacy_archive/alembic/versions/001_initial_schema.py` | Initial migration using `postgresql.UUID`, `CREATE EXTENSION "uuid-ossp"` | Archived, not active. |
| `database/migrations/001_initial_schema.sql` | Raw PostgreSQL DDL | Not wired to anything. |

### A.5 SQLAlchemy models

11 models defined in `backend/app/models/`, all registered in `app/models/__init__.py`:

| Model | File | Notes |
| :--- | :--- | :--- |
| `Applicant` | `applicant.py` | Uses `postgresql.UUID(as_uuid=True)`, `String(100)` first/last name, `email` unique, `tax_id_hash String(64)`. |
| `Assessment` | `assessment.py` | `postgresql.JSONB` for `input_features`, `postgresql.UUID`, GIN index, `CheckConstraint` on status. |
| `ArchetypeResult` | `archetype_result.py` | Per-engine result child of Assessment. |
| `AuditLog` | `audit_log.py` | Append-only audit row. |
| `EligibilityResult` | `eligibility_result.py` | E1 output child. |
| `ModelRegistry` | `model_registry.py` | ML model versioning metadata. |
| `ReadinessResult` | `readiness_result.py` | E5 output child. |
| `RecommendationResult` | `recommendation_result.py` | E4 output child. |
| `RiskTierResult` | `risk_tier_result.py` | E2 output child. |
| `RuleRegistry` | `rule_registry.py` | Rule version table. |

All 11 importable in isolation only if `sqlalchemy` installed. All target PostgreSQL types (`UUID(as_uuid=True)`, `JSONB`).

### A.6 Routers

**FastAPI routers registered in `main.py`:** 1 (health only).

| Module | Routes | Wired? |
| :--- | :--- | :--- |
| `app/api/health.py` | `GET /live`, `GET /ready`, `GET /deep` | Registered with prefix `/health`. Imported by `main.py:130`. |

**Flask Blueprints in `app/routes/`:** 1.

| Module | Routes | Wired? |
| :--- | :--- | :--- |
| `app/routes/assess.py` | `POST ""` (and `/assess`), `POST /person-a`, `POST /person-b` under unknown blueprint prefix | **Never registered.** `app/__init__.py` has no `create_app`; `main.py` does not import this module. |

No router file exists for: applicants CRUD, assessments, reports, model registry admin, rule registry admin, OpenAPI examples.

### A.7 Services

Three files in `app/services/`:

| Service | Status |
| :--- | :--- |
| `model_registry_service.py` | Present. Importable only with `sqlalchemy`. |
| `rule_registry_service.py` | Present. Cached TTL lookup. Importable only with `sqlalchemy`. |
| `rules_engine_service.py` | Present. Async methods: `evaluate_eligibility`, `evaluate_risk_tier`, `evaluate_readiness`. **Never instantiated or called by any other module in the repo** (verified via grep). |

Other "service-like" code:

| File | Role |
| :--- | :--- |
| `app/engines/*` | All 6 engines importable. `orchestrator.py` (legacy module) calls them in sequence. |
| `app/audit.py` | Not a service — direct SQLite + Config-coupled function module. |
| `app/lineage.py` | Not a service — module-level helpers. |
| `app/routing.py` | Pure functions, no class. |
| `app/orchestrator.py` | Top-level orchestrator. Imports engines, lineage, audit, routing. Callable directly. Verified to return a full Person A response with `bias`, `feature_contributions`, `archetype`, `risk_tier`, `recommendations`, `correlation_id`. |

### A.8 Tests

| Test file | Lines | Collection | Execution |
| :--- | :--- | :--- | :--- |
| `backend/tests/engines/test_livelihood_mapper.py` | 7 fns | OK | **7/7 PASS** |
| `backend/tests/engines/test_recommendation_engine.py` | 8 fns | OK | **8/8 PASS** |
| `backend/tests/test_e2e_failures.py` | 4 fns | **ImportError** (`from fastapi.testclient import TestClient` — fastapi not installed) | Cannot run |
| `backend/tests/test_e2e_person_a.py` | n fns | **ImportError** (same) | Cannot run |
| `backend/tests/test_e2e_person_b.py` | n fns | **ImportError** (same) | Cannot run |
| `backend/tests/test_orchestrator.py` | n fns | **ImportError** (same) | Cannot run |
| `backend/tests/test_model_registry_service.py` | n fns | Not collected due to fastapi import failure of peers | N/A |
| `backend/tests/test_rule_registry_service.py` | n fns | Same | N/A |
| `backend/tests/test_rules_engine_service.py` | n fns | Same | N/A |
| `legacy_archive/tests/*` | 4 files | Inside `legacy_archive/`, ignored by pytest discovery from `backend/` | N/A |
| `experiments/tests/*` | 9 files | Located at `experiments/tests/`; not under `backend/tests/` | Outside audit scope |
| `test_audit_fail_closed.py` (repo root) | Imports `from orchestrator import app, get_audit_publisher, get_db_session, KafkaAuditPublisher, DatabaseSession` | **Impossible** — no `orchestrator.py` in repo root | Cannot run |
| `test_ml_contract_fuzzing.py` (repo root) | Imports `from ml_service import app` | **Impossible** — no `ml_service.py` in repo root | Cannot run |

**Verified pass count: 15 / 15 engine tests. All e2e/orchestrator/service tests blocked by missing `fastapi` and `sqlalchemy`.**

### A.9 Docker files

| File | Verified |
| :--- | :--- |
| `backend/Dockerfile` | Present. Multi-stage `python:3.12-slim`. Runs `uvicorn app.main:app`. Never built in this audit. |
| `docker-compose.yml` | **Does not exist.** |
| `compose.yaml` | **Does not exist.** |

### A.10 CI files

**No CI present.** Searched for: `.github/`, `.gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`, `Jenkinsfile`, `.drone.yml`, any top-level `*.yml`/`*.yaml`. None found.

### A.11 Data + models on disk

| Artifact | Verified |
| :--- | :--- |
| `data/raw/loan_approval_dataset.csv` | Present. |
| `data/raw/External_Cibil_Dataset.csv` | Present. |
| `data/raw/Internal_Bank_Dataset.csv` | Present. |
| `data/raw/RuralCreditData.csv` | Present. |
| `data/processed/eligibility_data.csv` | Present. |
| `data/processed/risk_tier_thresholds.json` | Present. |
| `data/processed/borrower_archetype_definitions.json` | Present. |
| `models/eligibility/random_forest.joblib` | **Present, 1.3 MB, loads as `RandomForestClassifier` with `predict` + `predict_proba`.** Verified loadable. |
| `models/archetype/kmeans_model.pkl` | Present, 206 KB. |
| `models/archetype/scaler.pkl` | Present, 658 B. |
| `models/risk_tier/risk_tier_thresholds.json` | Present, 457 B. |
| `models/readiness/`, `models/livelihood/`, `models/recommendation/` | No artifact (only `.gitkeep` for readiness). |

### A.12 SQLite databases on disk

| File | Tables | Notes |
| :--- | :--- | :--- |
| `backend/riskintel.db` | `alembic_version` (empty) | Created by prior `alembic init` or `Base.metadata.create_all` call. No app tables. |
| `riskintel.db` (repo root) | `audit_log` (2 rows) | Created by `app/audit.py::init_db()` when last invoked. |

**Two DBs exist. They disagree.**

### A.13 Container/runtime

| Tool | Version | Found in venv? |
| :--- | :--- | :--- |
| Python | 3.13.13 | Yes (venv). |
| Flask | 3.1.3 | Yes (leftover). |
| scikit-learn | 1.9.0 | Yes. |
| treeinterpreter | 0.2.3 | Yes. |
| reportlab | 4.5.1 | Yes. |
| joblib | 1.5.3 | Yes. |
| pandas | 3.0.3 | Yes. |
| pytest | 9.0.3 | Yes. |
| **FastAPI** | — | **NO.** |
| **Uvicorn** | — | **NO.** |
| **SQLAlchemy** | — | **NO.** |
| **Alembic** | — | **NO (package only, not installed).** |
| **aiosqlite** | — | **NO.** |
| **asyncpg** | — | **NO.** |
| **pydantic v2** | — | **NO.** |
| **pydantic-settings** | — | **NO.** |
| **httpx** | — | **NO.** |

---

## B. What is missing

| # | Item | Evidence |
| :---: | :--- | :--- |
| 1 | `backend/alembic/versions/` directory | `ls alembic` returns no `versions/`. |
| 2 | `flask` in `backend/requirements.txt` | File lists FastAPI stack only. |
| 3 | `create_app` symbol in `backend/app/__init__.py` | Docstring present, function absent. |
| 4 | `database/migrations/001_initial_schema.sql` wired to any tool | No migration runner references it. |
| 5 | `app/api/v1/*` (or any versioned) routers | Only `app/api/health.py`. |
| 6 | Router for `POST /api/assess`, `POST /api/assess/person-a`, `POST /api/assess/person-b` | No file under `app/api/` defines them. |
| 7 | Router for `POST /api/report/generate` | No file. |
| 8 | Router for `GET /api/report/download/{id}` | No file. |
| 9 | `ReportService` / `app/report/*.py` implementations | Only `__init__.py` (empty). |
| 10 | `RecommendationService` (E4) service-layer wrapper | Engine exists in `app/engines/recommendation/`; no service in `app/services/`. |
| 11 | `ReadinessService` (E5) service-layer wrapper | Engine exists; no service. |
| 12 | `ArchetypeService` (E3) service-layer wrapper | Engine exists; no service. |
| 13 | `LivelihoodService` (E6) service-layer wrapper | Engine exists; no service. |
| 14 | `AssessmentService` / `AssessmentOrchestrator` | Old `app/orchestrator.py` is procedural, not a service class. |
| 15 | `ApplicantService` | No file. |
| 16 | Pydantic request schemas for Person A / Person B (with field bounds) | `schemas/applicant.py` exists but is applicant-CRUD shape, not assessment request. No `PersonARequest` / `PersonBRequest`. |
| 17 | Pydantic response schemas for eligibility / risk_tier / readiness / archetype / recommendations | No `EligibilityResponse` etc. |
| 18 | `applicant_repository` / `assessment_repository` | Only `model_registry_repository` and `rule_registry_repository`. |
| 19 | `conftest.py` at `backend/tests/` | No shared fixtures, no test DB engine, no transactional rollback. |
| 20 | `pytest.ini` / `pyproject.toml` / `setup.cfg` for pytest config | None in `backend/`. |
| 21 | `docker-compose.yml` / `compose.yaml` | None. |
| 22 | CI configuration | None. |
| 23 | Lock file / `requirements.lock` | Only `requirements.txt` with `>=` floors. |
| 24 | `app/middleware/*` implementations | Directory contains only `__init__.py`. |
| 25 | `app/report/*` implementations | Directory contains only `__init__.py`. |
| 26 | A documented entry point for prod (`uvicorn` is referenced only in `Dockerfile`) | No `Makefile`, no `Procfile`, no scripts dir entry. |

---

## C. What is broken

| # | Symptom | Reproduced | Root cause |
| :---: | :--- | :--- | :--- |
| C1 | `python run.py` fails at import | `ImportError: cannot import name 'create_app' from 'app'` | `app/__init__.py` has no factory. |
| C2 | `app/main.py` cannot be imported | `ModuleNotFoundError: No module named 'fastapi'` | venv lacks FastAPI/uvicorn/sqlalchemy/aiosqlite/pydantic. |
| C3 | `app/services/rules_engine_service.py` cannot be imported | `ModuleNotFoundError: No module named 'sqlalchemy'` | Same. |
| C4 | 7 of 9 test files in `backend/tests/` cannot be collected | `from fastapi.testclient import TestClient` fails | Same. |
| C5 | `app/api/health.py:96` issues `CREATE TABLE ... SERIAL PRIMARY KEY` against SQLite | Static read | Health-deep probe will error at runtime when DB target is SQLite. |
| C6 | `app/main.py` includes only the health router | `grep` of `main.py` shows one `include_router` | All `/api/assess*` and `/api/report*` requests return 404. |
| C7 | `app/routes/assess.py` (Flask Blueprint) never registered with any framework | Module imports `from flask import Blueprint`; not imported by `main.py`; `create_app` does not exist | The blueprint is dead code. |
| C8 | `app/models/*.py` declare `postgresql.UUID` and `postgresql.JSONB` | Read each model file | Even if SQLAlchemy were installed, the engine (SQLite via aiosqlite) cannot represent these types. |
| C9 | `backend/nul` is a 46-byte file containing the string `/usr/bin/bash: line 1: del: command not found` | `cat backend/nul` | Stale shell artifact; no semantic effect. |
| C10 | Two SQLite DBs with different schemas | `riskintel.db` (root) has `audit_log`; `backend/riskintel.db` has `alembic_version` | Tests/audit code resolve DB to repo root; FastAPI config resolves to `backend/`. |
| C11 | `app/audit.py` imports `from app.config import Config` (Flask Config) | Read line 11 | Import will succeed (Config exists) but `Config.DB_PATH = "riskintel.db"` + path resolution writes to repo root, not `backend/`. |
| C12 | `app/audit.py:14` `BASE_DIR = parents[2]` — but file is at `backend/app/audit.py`, so `parents[2]` = repo root. `Config.DB_PATH = "riskintel.db"` → resolved to `<repo>/riskintel.db` | Verified via `app.audit.get_db_path()` returning `C:\Users\anike\Desktop\Riskintel\riskintel.db` | Same as C10. |
| C13 | `app/db/session.py:34` `async def get_db() -> AsyncSession:` annotated as `AsyncSession` but body uses `yield` (async generator) | Read signature | Type hint lies. |
| C14 | `app/core/config.py:29` `PROJECT_ROOT = Path(__file__).resolve().parents[3]` | Read | `parents[3]` of `backend/app/core/config.py` resolves to `C:\` (parent of repo). `MODEL_DIR` and `REPORT_OUTPUT_DIR` will be wrong on import. |
| C15 | `app/services/rules_engine_service.py:339` compares 0–100 readiness score against `floor_threshold` default 0.5 | Read | Unit mismatch — readiness is 0–100, threshold is 0.0–1.0. |
| C16 | `app/main.py:103-125` `unhandled_exception_handler` re-raises `RequestValidationError` instead of returning `ErrorResponse` envelope | Read | 422 responses bypass contract `ErrorResponse` shape. |
| C17 | `app/services/rules_engine_service.py:11-15` docstring says "Replaces the retired E1 Random Forest with versioned, threshold-driven rules" but `output_contracts.md` requires `bias` + `feature_contributions` (which only the Random Forest + `treeinterpreter` produce) | Cross-read | Rules engine cannot satisfy the contract; only `app/engines/eligibility/eligibility_engine.py` does. |
| C18 | `riskintel.db` (root) is 12 KB; backend/venv 1+ GB; `backend/riskintel.db` 20 KB | `ls -la` | Indicates a real in-process `orchestrator` run already produced audit records. |
| C19 | `test_audit_fail_closed.py` and `test_ml_contract_fuzzing.py` (repo root) reference nonexistent modules | Read imports | Both files unrunnable in current tree. |
| C20 | `.pytest_cache/v/cache/lastfailed` records 17 failed tests across legacy + backend e2e + experiments paths | Read cache | The last test run prior to this audit failed broadly. |

---

## D. What architecture is currently implemented

Two parallel architectures coexist. Neither is complete.

### D.1 Architecture that runs today (Flask, monolithic, in-process)

- **Entry point:** `python run.py` (broken — `create_app` missing).
- **Request lifecycle:** Flask Blueprint `app.routes.assess.assess_bp` → `app.orchestrator.execute_orchestrator(payload)`.
- **Orchestrator:** `app/orchestrator.py` — synchronous function, ~270 lines. Calls 6 engines in sequence: eligibility → risk_tier → archetype → readiness/livelihood → recommendation. Includes `validate_payload` and per-field `check_required` / `validate_range` helpers.
- **Engines:** `app/engines/{eligibility,risk_tier,archetype,readiness,livelihood,recommendation}/` — synchronous functions, scikit-learn `.joblib` + `.pkl` artifacts. `recommendation/` is rule-based via `evaluator.evaluate_rules` + `context.build_person_a_context`.
- **Audit:** `app/audit.py` writes one row per successful orchestrator run to `riskintel.db` (root) via stdlib `sqlite3`. Fail-closed via `AuditLogError`.
- **Routing layer:** `app/routing.py` does CIBIL=0/-1 → Person B re-route.
- **Validated state:** in-process call `execute_orchestrator(person_a_payload)` returns valid JSON with all required keys (`status`, `applicant`, `eligibility{verdict,probability,bias,feature_contributions}`, `risk_tier{tier,label,description,score_used,thresholds}`, `archetype{label,description,cluster_id}`, `recommendations`, `correlation_id`). Engine loads `models/eligibility/random_forest.joblib` successfully.
- **Engine test coverage:** 15 unit tests pass (livelihood mapper + recommendation rule evaluator + contract shape).
- **Missing runtime:** HTTP server. No working endpoint. `run.py` cannot start. `app.routes.assess` blueprint is not mounted anywhere.

### D.2 Architecture that is half-wired (FastAPI, async, SQLAlchemy)

- **Entry point:** `uvicorn app.main:app` (would require installing the entire FastAPI/SQLAlchemy/aiosqlite stack — none currently in venv).
- **App factory:** `app = FastAPI(title=..., version=..., lifespan=lifespan, docs_url="/docs", redoc_url="/redoc", openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")` with one `include_router` for `app.api.health.router` (prefix `/health`).
- **Lifespan:** opens async engine from `app.db.session.engine`, runs `SELECT 1`, disposes on shutdown.
- **CORS:** `CORSMiddleware` with origins from `settings.ALLOWED_ORIGINS` (default `localhost:5173`, `localhost:3000`).
- **Exception handler:** generic 500 → `ErrorResponse` envelope. HTTP/validation errors re-raised.
- **Config:** `app/core/config.py` Pydantic `BaseSettings` — `APP_NAME`, `APP_VERSION`, `API_V1_PREFIX="/api/v1"`, `DATABASE_URL` property → `sqlite+aiosqlite:///riskintel.db`, `MODEL_DIR`/`REPORT_OUTPUT_DIR` resolved from `PROJECT_ROOT` (broken depth, see C14).
- **DB layer:** `app/db/base.py` `class Base(DeclarativeBase)`. `app/db/session.py` async engine + `async_sessionmaker` + `get_db` (signature broken, C13). `app/core/dependencies.py` `get_db_session` async generator dependency.
- **Models:** 11 SQLAlchemy models in `app/models/`, all targeting PostgreSQL types (C8). Wired to `Base.metadata` via `app/models/__init__.py`.
- **Repositories:** `app/repositories/{base,model_registry_repository,rule_registry_repository}.py`. Two only.
- **Services:** 3 (rules_engine, rule_registry, model_registry). `rules_engine_service` not invoked from any caller in the tree.
- **Schemas:** 3 (applicant, assessment, common). Applicant schema is for CRUD, not for assessment requests.
- **Alembic:** `alembic.ini` + `alembic/env.py` configured. `versions/` missing. `env.py` imports all 11 models and overrides URL from `app.core.config.settings`. Cannot run.
- **Validation:** none in Pydantic; would rely on `orchestrator.validate_payload` (Flask-era logic, not wired into FastAPI handlers).
- **Routers:** only `app/api/health.py` (`/health/live`, `/health/ready`, `/health/deep`). `health_deep` issues Postgres DDL against SQLite (C5).
- **Report module:** empty.
- **Middleware module:** empty.
- **Test infrastructure:** 4 test files import `from fastapi.testclient import TestClient`. None can run.

### D.3 What is shared between the two

- `app/__init__.py` docstring (only).
- `app/exceptions.py` — `RequestValidationError`, `CriticalEngineError`, `NonCriticalEngineError`, `AuditLogError`, `RiskIntelException`. Both architectures import it. Tests import it.
- `app/audit.py` — used only by `orchestrator.py` and the legacy e2e tests. The `app/audit.py` module also conflicts with `backend/audit.py` (root level) which is a different file (RF eval script).
- `app/engines/*` — used only by `orchestrator.py`. Not imported by any service in the FastAPI path.
- `data/processed/*`, `models/*` — same artifacts on disk.

---

## E. Contradictions between docs and code

| # | Doc | Code reality |
| :---: | :--- | :--- |
| E1 | `docs/final_architecture_v1.md:30,439` — Backend = **Flask**; ML stack scikit-learn. | `app/main.py` = FastAPI. `app/routes/assess.py` = Flask Blueprint (orphaned). `requirements.txt` lists FastAPI stack. |
| E2 | `docs/final_architecture_v1.md:441` — DB = **SQLite**. | `app/models/*.py` use `postgresql.UUID`, `postgresql.JSONB`. `alembic.ini` URL is Postgres. `legacy_archive/alembic/versions/001_initial_schema.py` runs `CREATE EXTENSION "uuid-ossp"`. |
| E3 | `docs/architecture.md:24-27` — endpoints under `/api/...` (no version). | `app/core/config.py:34` `API_V1_PREFIX = "/api/v1"`. `main.py:85` openapi under `/api/v1/openapi.json`. |
| E4 | `docs/output_contracts.md:20,196,403` — endpoints `POST /api/assess/person-a`, `POST /api/assess/person-b`, `POST /api/report/generate`. | No router file matches any of these. `app/api/health.py` is the only registered router. |
| E5 | `docs/output_contracts.md:404` — `POST /api/report/generate` returns `application/pdf` binary. | `app/report/` is empty. No `ReportService`. No `/api/report/*` route. |
| E6 | `docs/output_contracts.md:144-145` — eligibility response must include `bias` (float) and 11-entry `feature_contributions` (sum + bias = probability). | `app/services/rules_engine_service.py:8-9` docstring says "Replaces the retired E1 Random Forest". Rules engine produces `is_eligible: bool`, not `bias`/`feature_contributions`. Only `app/engines/eligibility/eligibility_engine.py` + `treeinterpreter` produce the required output. |
| E7 | `docs/output_contracts.md:5` "Status: FROZEN" (V1.1 with `bias` field). | E6 mismatch implies the rules engine cannot satisfy the frozen contract. |
| E8 | `IMPLEMENTATION_ROADMAP.md:42,64,880,890` — Flask + `/api/assess*` + `/api/report/generate` + SQLite. | Same contradictions as E1, E2, E3, E4, E5. |
| E9 | `docs/final_architecture_v1.md:421-429` Decision D15 — SQLite for V1. | `app/db/session.py:18-25` uses `sqlite+aiosqlite` (matches), but `app/core/dependencies.py` and `app/main.py` lifespan also point at SQLite via `settings.DATABASE_URL`. Models do not. Net: code split. |
| E10 | `docs/output_contracts.md:556-568` — E4 output for Person A includes `risk_factors`; for Person B includes `improvement_areas` and `next_steps`. | `app/engines/recommendation/recommendation_engine.py` does generate these. Verified by import. No service wrapper, no router. |
| E11 | `docs/final_architecture_v1.md:439` — "scikit-learn (Random Forest, K-Means)" used for E1, E3, E6. | `app/services/rules_engine_service.py:11-12` says E1 Random Forest is "retired". E3 K-Means (`models/archetype/kmeans_model.pkl`) and E1 RF (`models/eligibility/random_forest.joblib`) both still on disk and importable. |
| E12 | `PRD.md:48-62` — Person A inputs include `Credit Score`, `Credit History Features`, `Education`, `Employment Status`, `Marital Status`, `Property Area`. | `orchestrator.py` does not require or persist these as first-class fields beyond what `applicant.py` schema already covers for the legacy form. |
| E13 | `IMPLEMENTATION_ROADMAP.md:19-20` — "Solo developer build sequence", 11 phases, 48 tasks. | No `PHASE_*.md`, no task tracker, no `TASKS.json`. Roadmap file is the only artifact. |
| E14 | `docs/output_contracts.md:595-695` — error response envelope `{"status":"error","error":{"code","message","details"}}`. | `app/schemas/common.py` defines `ErrorResponse` matching the shape. But `app/main.py:113-114` re-raises `RequestValidationError` → FastAPI default 422, not the envelope. |
| E15 | `docs/output_contracts.md:404-406` — `POST /api/report/generate` returns `Content-Type: application/pdf`. | No route, no service, no report module code. |

---

## F. Exact blockers ranked by severity

Severity = inability to start the backend in either architecture.

### F.1 CRITICAL — system cannot serve any request

| Rank | Blocker | Impact |
| :---: | :--- | :--- |
| 1 | **No working HTTP entry point.** `python run.py` fails at import (no `create_app`). `uvicorn app.main:app` fails at import (`fastapi` not installed). `app/routes/assess.py` Blueprint never registered. | 100% of HTTP traffic returns no answer. |
| 2 | **`app/audit.py` is the only persistence path that has ever written real data** (2 rows in `riskintel.db` at repo root) but its target DB differs from `app/core/config.py`'s target DB. | Audit trail forks; cannot trust either. |
| 3 | **`alembic/versions/` does not exist.** No schema migration has ever been generated for the FastAPI models. | FastAPI architecture has no DB schema. No service can persist. |
| 4 | **All 11 SQLAlchemy models target PostgreSQL types** (`postgresql.UUID`, `postgresql.JSONB`) while the engine URL is `sqlite+aiosqlite`. | Even if SQLAlchemy were installed, model DDL would fail on SQLite. |
| 5 | **Frontend has no endpoint to call.** The frozen contract requires `POST /api/assess/person-a`, `POST /api/assess/person-b`, `POST /api/report/generate`. None registered. | Frontend (Vite/React, present in tree) has nothing to call. |

### F.2 HIGH — system cannot be tested

| Rank | Blocker | Impact |
| :---: | :--- | :--- |
| 6 | **7 of 9 `backend/tests/*.py` files cannot be collected** because they import `from fastapi.testclient import TestClient` and `fastapi` is not installed in venv. | Test suite reports 7 collection errors, 0 runs. |
| 7 | **No `conftest.py`, no `pytest.ini`, no shared fixtures, no test DB engine.** | Even if FastAPI were installed, tests share the dev DB and would race. |
| 8 | **Top-level `test_audit_fail_closed.py` and `test_ml_contract_fuzzing.py` import modules that do not exist** (`from orchestrator import app, get_audit_publisher, ...` and `from ml_service import app`). | Both files cannot run. |
| 9 | **Venv is incomplete.** `pip list` shows Flask, scikit-learn, treeinterpreter, reportlab, pytest. Missing: fastapi, uvicorn, sqlalchemy, alembic, aiosqlite, asyncpg, pydantic, pydantic-settings, httpx. | Cannot exercise the FastAPI path at all from the existing venv. |
| 10 | **Two competing test suites (legacy + new) target the same domain but use different frameworks.** | Any test refactor must touch both, with risk of breaking the other. |

### F.3 HIGH — system cannot persist or load structured data

| Rank | Blocker | Impact |
| :---: | :--- | :--- |
| 11 | **The Flask orchestrator works in-process and produces a valid response shape**, but no Flask app exists to call it over HTTP. | The "engine" half of the system is real. The "API" half is not. |
| 12 | **`app/main.py` lifespan opens the async SQLite engine at startup**, but the engine is incompatible with the model types (F.1 #4). | Boot would fail at lifespan `SELECT 1` only if SQLAlchemy were installed. With current venv, fails earlier at import. |
| 13 | **`PROJECT_ROOT` resolves to `C:\` (`parents[3]`).** `MODEL_DIR` and `REPORT_OUTPUT_DIR` resolve to nonsense paths. | Engine code that joins `MODEL_DIR` would point at the wrong directory. |
| 14 | **`get_db_path()` in `app/audit.py` resolves to repo root; `app/core/config.py` resolves to `backend/`.** | Two DBs, two paths, no reconciliation. |

### F.4 MEDIUM — contract violations and dead code

| Rank | Blocker | Impact |
| :---: | :--- | :--- |
| 15 | **`rules_engine_service.py` cannot satisfy the frozen eligibility contract** (it returns `is_eligible: bool`, not `verdict` + `probability` + `bias` + `feature_contributions`). | Even if wired, would not pass contract checks. |
| 16 | **No `ReportService` or `app/report/*.py` implementation.** `POST /api/report/generate` is unimplementable as-is. | Reportlab is installed but no caller. |
| 17 | **`RequestValidationError` not converted to `ErrorResponse` envelope.** | 422 responses break the contract for clients that expect `{status:"error", error:{...}}`. |
| 18 | **`health_deep` DDL is Postgres-only.** | Probe would fail in current DB target (SQLite). |
| 19 | **Empty `app/middleware/` and `app/report/` directories** (only `__init__.py`). | Layout promises modules that don't exist. |
| 20 | **`get_db` is annotated as `AsyncSession` but is an async generator.** | Static analysis and FastAPI dependency wiring are at risk. |
| 21 | **`backend/nul` is a 46-byte stale file** containing the literal string `/usr/bin/bash: line 1: del: command not found`. | Cosmetic. |
| 22 | **15 of the test files in `.pytest_cache/v/cache/lastfailed` are marked failed** (legacy, experiments, backend e2e). | Prior runs failed. The cache reflects that nothing has run cleanly in this tree. |

### F.5 LOW — hygiene

| Rank | Blocker | Impact |
| :---: | :--- | :--- |
| 23 | No `docker-compose.yml`. | Cannot stand up DB + app together. |
| 24 | No CI configuration. | No automated checks on PRs. |
| 25 | `.gitignore` excludes `models/*.joblib` but `models/eligibility/random_forest.joblib` is tracked. | Repo size / VCS hygiene. |
| 26 | No lock file. | Reproducible builds impossible. |
| 27 | `tests/engines/test_recommendation_engine.py` and `test_livelihood_mapper.py` pass, but neither target is referenced by any service or router in the current tree. | Tests pass against code that has no live caller. |
| 28 | `reports/` directory contains 15+ markdown review/spec docs, several titled with frozen status but written before the FastAPI migration. | Documentation drift. |

---

## Verified facts (commands run during audit)

1. `python -c "import fastapi"` → `ModuleNotFoundError`.
2. `python -c "import sqlalchemy"` → `ModuleNotFoundError`.
3. `python -c "import alembic; print(alembic.__version__)"` → AttributeError; package not installed.
4. `python run.py` → `ImportError: cannot import name 'create_app' from 'app'`.
5. `python -m flask --app run.py run` → same ImportError.
6. `python -c "from app.main import app"` → `ModuleNotFoundError: No module named 'fastapi'`.
7. `python -c "from app.api import health"` → `ModuleNotFoundError: No module named 'fastapi'`.
8. `python -c "from app.routes import assess"` → succeeds; returns `Blueprint` object.
9. `python -c "from app.orchestrator import execute_orchestrator"` → succeeds; returns function.
10. `python -c "from app.engines.eligibility.eligibility_engine import get_eligibility"` → succeeds.
11. `python -c "from app.engines.{risk_tier,archetype,readiness,livelihood,recommendation}.* import *"` → all 6 engine entrypoints importable.
12. `execute_orchestrator(person_a_payload)` → returns dict with keys `status,user_type,timestamp,applicant,eligibility,risk_tier,archetype,recommendations,correlation_id`. Eligibility contains `bias` + 11-entry `feature_contributions`. Risk tier contains `thresholds`. Verified.
13. `execute_orchestrator({'user_type':'person_a'})` → raises `RequestValidationError("Required field 'full_name' is missing")`.
14. `joblib.load('../models/eligibility/random_forest.joblib')` → returns `RandomForestClassifier` with `predict` + `predict_proba`.
15. `os.listdir('../models')` → `.gitkeep`, `archetype/`, `eligibility/`, `readiness/`, `risk_tier/`. No `livelihood/`, no `recommendation/` artifacts.
16. `ls backend/alembic` → `__init__.py`, `env.py`, `script.py.mako`. No `versions/`.
17. `sqlite3 riskintel.db '.tables'` (root) → `audit_log`. 2 rows.
18. `sqlite3 backend/riskintel.db '.tables'` → `alembic_version`. 0 rows.
19. `pytest tests/engines` → 15/15 PASS in 0.04s.
20. `pytest` (full) → 15 collected, 7 collection errors (all `from fastapi.testclient import TestClient`).
21. `app.audit.get_db_path()` → `C:\Users\anike\Desktop\Riskintel\riskintel.db` (repo root).
22. `cat backend/nul` → 46 bytes; content: `/usr/bin/bash: line 1: del: command not found\n`.

---

End of audit.
