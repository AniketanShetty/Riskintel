# Drift Remediation Plan

**Date:** 2026-06-06
**Engineer:** Principal Backend Refactoring
**Constraint:** Preserve `execute_orchestrator()`, RandomForest integration, 15 passing engine tests, frozen output contracts. Minimize churn. No new features.

---

## Ground truth (from audit)

- `app.orchestrator.execute_orchestrator()` — works, returns contract-shaped response.
- `models/eligibility/random_forest.joblib` — loads, used by `app/engines/eligibility/eligibility_engine.py`.
- 15/15 tests pass under `backend/tests/engines/`.
- `app/main.py` (FastAPI) does not boot — fastapi absent + 1 router + no DB schema.
- `app/routes/assess.py` (Flask Blueprint) not registered anywhere.
- `app/db/session.py` + `app/models/*` + Alembic target PostgreSQL types; engine URL targets SQLite. Incompatible.
- Two DBs on disk: `riskintel.db` (root, `audit_log`), `backend/riskintel.db` (`alembic_version`).
- 7 of 9 `backend/tests/*.py` cannot be collected (fastapi missing).
- `requirements.txt` lists FastAPI stack; venv has Flask leftovers, no FastAPI/SQLAlchemy/alembic.

---

## Strategic decision (must precede all code)

**Lock the framework to FastAPI.** Reason: `Dockerfile` already runs `uvicorn app.main:app`; `app/main.py`, `app/api/`, `app/core/`, `app/db/`, `app/models/`, `app/repositories/`, `app/schemas/`, `alembic/`, `requirements.txt`, `.env.example` all assume FastAPI. Flask path is dead (`create_app` missing, Blueprint not registered). Flask-era executable code that **works** = `app/orchestrator.py` and `app/engines/*`. These do not import Flask; they are framework-agnostic Python. **Decision: keep FastAPI, delete Flask remnants, mount `execute_orchestrator` under a FastAPI route.**

**Lock the DB to SQLite.** Reason: `riskintel.db` already exists with `audit_log` rows; SQLite is in the frozen arch D15; `app/db/session.py` uses `sqlite+aiosqlite`. Decision: drop all `postgresql.UUID`/`postgresql.JSONB` types, replace with generic SQLAlchemy types compatible with SQLite.

---

## 1. Exact file modifications

### 1.1 `backend/requirements.txt` — add missing deps

Add (current file lists them but venv has none installed):

```
aiosqlite>=0.20.0
sqlalchemy[asyncio]>=2.0.35
alembic>=1.13.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
```

Effort: trivial. Risk: none. Rollback: remove lines.

### 1.2 `backend/app/core/config.py` — fix `PROJECT_ROOT` depth

Change `parents[3]` → `parents[2]`. `backend/app/core/config.py` → `parents[0]=app`, `parents[1]=backend`, `parents[2]=repo_root`. Currently resolves to `C:\`.

Effort: 1 line. Risk: low. Touches path resolution only. Rollback: revert line.

### 1.3 `backend/app/db/session.py` — fix `get_db` annotation

Replace `-> AsyncSession:` with `-> AsyncGenerator[AsyncSession, None]:`. Body already uses `yield`.

Effort: 1 line. Risk: none (type hint only). Rollback: revert.

### 1.4 `backend/app/models/*.py` — strip PostgreSQL types

Files to touch: all 11 in `app/models/`. Pattern: `from sqlalchemy.dialects.postgresql import ...` → delete or use generic. `postgresql.UUID(as_uuid=True)` → `String(36)` (UUID stored as hex string). `postgresql.JSONB` → `JSON` from `sqlalchemy`. Drop `Index(..., postgresql_using="gin")` in `assessment.py:83`.

Specific edits:

- `applicant.py:14` — `postgresql.UUID` → `String(36)`. Update `mapped_column(UUID(as_uuid=True), ...)` to `mapped_column(String(36), ...)`.
- `assessment.py:14` — `postgresql.JSONB, postgresql.UUID` → `JSON, String`. Drop GIN index line 83.
- `archetype_result.py`, `eligibility_result.py`, `readiness_result.py`, `recommendation_result.py`, `risk_tier_result.py` — same swap (each uses `postgresql.UUID` for FK + parent PK).
- `audit_log.py` — same UUID swap.
- `model_registry.py`, `rule_registry.py` — same UUID swap.

Effort: ~30 line edits across 11 files. Risk: medium (changes DB schema). Rollback: revert file by file.

### 1.5 `backend/app/main.py` — replace exception handler

Lines 103-125. Replace `if isinstance(exc, (HTTPException, RequestValidationError)): raise` with: also catch `RequestValidationError` and return `ErrorResponse` envelope with status 400, code `VALIDATION_ERROR`, `details` from `exc.errors()`. Keep `HTTPException` re-raise.

Effort: 15 lines. Risk: low. Contract change to one error class only. Rollback: revert.

### 1.6 `backend/app/api/health.py` — fix Postgres DDL in `health_deep`

Lines 96-98. Replace `CREATE TABLE IF NOT EXISTS _health_test (id SERIAL PRIMARY KEY, val TEXT)` with `CREATE TABLE IF NOT EXISTS _health_test (id INTEGER PRIMARY KEY AUTOINCREMENT, val TEXT)`. Drop `SERIAL`. (SQLite-compatible.)

Effort: 1 line. Risk: none. Rollback: revert.

### 1.7 `backend/app/audit.py` — point at `backend/` not repo root

Line 14: `BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`. From `backend/app/audit.py` → `parents[2]` = repo root. Change to `parents[1]` = `backend/`. Or: read DB path from `app.core.config.settings` instead of `Config`.

Effort: 1-2 lines. Risk: low (resolves to `backend/riskintel.db` which already exists). Rollback: revert.

### 1.8 `backend/alembic/env.py` — point at `Base` only

Already imports all 11 models. After model edits (1.4), no change needed here. **Skip unless `import` fails.**

### 1.9 `backend/app/services/rules_engine_service.py:339` — fix threshold unit

Either:
- (a) Change default `financial_health_floor_threshold` from `0.5` to `50` AND multiply by 100 at compare site.
- (b) Change compare site to `(financial_health_score / 100) < floor_threshold`.

Pick (b). 1-line edit.

Effort: 1 line. Risk: low (engine behavior change for floor cases only). Rollback: revert.

### 1.10 `backend/app/core/dependencies.py` — none

Already correct. **Skip.**

---

## 2. Exact file deletions

| File | Reason | Effort | Risk |
| :--- | :--- | :--- | :--- |
| `backend/app/routes/assess.py` | Dead Flask Blueprint, never imported by anything that runs. | trivial | none |
| `backend/app/routes/__init__.py` | Empty after deletion above. | trivial | none |
| `backend/app/routes/` | Empty directory. | trivial | none |
| `backend/app/middleware/__init__.py` | Empty, no other files. | trivial | none |
| `backend/app/middleware/` | Empty directory. | trivial | none |
| `backend/app/report/__init__.py` | Empty, no implementations. | trivial | none |
| `backend/app/report/` | Empty directory. | trivial | none |
| `backend/app/config.py` | Old Flask `Config` class. Replaced by `app/core/config.py`. Not imported by anything that runs (only by `app/audit.py:11` which is itself legacy). | trivial | low — must remove the import in `app/audit.py` first |
| `backend/run.py` | Flask entry; `create_app` missing. Dead. | trivial | none |
| `backend/audit.py` (root level) | RF eval script, not the audit module. Not imported. | trivial | none |
| `backend/nul` | Stale shell artifact, 46 bytes of error message. | trivial | none |
| `legacy_archive/` | Whole directory. | trivial | none (already archived, ignored by VCS) |
| `riskintel.db` (repo root) | Wrong location for audit log. After `app/audit.py` fix (1.7), this file is dead. | trivial | low — 2 audit rows lost (acceptable, schema stays) |
| `test_audit_fail_closed.py` (repo root) | Imports nonexistent `orchestrator` module. | trivial | none |
| `test_ml_contract_fuzzing.py` (repo root) | Imports nonexistent `ml_service`. | trivial | none |

**Total deletions: 14 files / directories. 1 file with minor risk (root `riskintel.db`, 2 audit rows).**

---

## 3. Exact dependency additions

Install into `backend/venv`:

```bash
cd backend && venv/Scripts/python.exe -m pip install -r requirements.txt
```

The 9 packages listed in §1.1 are not present in the current venv (verified: `pip list` returned only pytest from that group). After install, `app/main.py` and `app/db/session.py` and `app/services/*` become importable.

Risk: low. Standard pip resolution.

---

## 4. Exact route registration work

### 4.1 New file: `backend/app/api/v1/__init__.py`

Empty package marker.

### 4.2 New file: `backend/app/api/v1/assess.py`

```python
from fastapi import APIRouter, Request
from app.orchestrator import execute_orchestrator

router = APIRouter(prefix="/assess", tags=["assess"])

@router.post("")
@router.post("/assess")
async def assess(request: Request):
    payload = await request.json()
    return execute_orchestrator(payload)

@router.post("/person-a")
async def assess_person_a(request: Request):
    payload = await request.json()
    payload["user_type"] = "person_a"
    return execute_orchestrator(payload)

@router.post("/person-b")
async def assess_person_b(request: Request):
    payload = await request.json()
    payload["user_type"] = "person_b"
    return execute_orchestrator(payload)
```

Imports `execute_orchestrator` from the existing, working module. No new logic. 4 routes.

Effort: ~25 lines new file. Risk: low (calls into already-working function). Rollback: delete file + revert `main.py` include.

### 4.3 New file: `backend/app/api/v1/reports.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter(prefix="/report", tags=["report"])

@router.post("/generate")
async def generate_report(payload: dict):
    # Minimal stub: return 501 until ReportService exists
    raise HTTPException(status_code=501, detail="Report generation not yet implemented")

@router.get("/download/{report_id}")
async def download_report(report_id: str):
    raise HTTPException(status_code=501, detail="Report download not yet implemented")
```

Stub only. Marks contract endpoints as present but unimplemented. Allows e2e tests to assert 501.

Effort: 15 lines. Risk: none (no behavior, just registers route shape). Rollback: delete.

### 4.4 Modify `backend/app/main.py:128-132`

Add imports + includes:

```python
from app.api.health import router as health_router
from app.api.v1.assess import router as assess_v1_router
from app.api.v1.reports import router as reports_v1_router

app.include_router(health_router, prefix="/health")
app.include_router(assess_v1_router, prefix="/api")
app.include_router(reports_v1_router, prefix="/api")
```

Also change `API_V1_PREFIX` default in `core/config.py:34` from `/api/v1` to `/api` (matches frozen contract). Or change openapi_url line to use bare prefix.

Effort: 6 lines. Risk: low. Rollback: revert.

**Total routes added: 4 (assess) + 2 (report stubs) = 6 endpoints registered.**

---

## 5. Exact migration generation sequence

After §1.4 model edits are in place and §3 deps installed:

1. `cd backend`
2. `alembic revision --autogenerate -m "initial schema"` — produces `alembic/versions/<rev>_initial_schema.py`.
3. Inspect generated file. Confirm `applicants`, `assessments`, `archetype_results`, `audit_logs`, `eligibility_results`, `model_registry`, `readiness_results`, `recommendation_results`, `risk_tier_results`, `rule_registry` are present.
4. `alembic upgrade head` against `backend/riskintel.db`.
5. Verify: `sqlite3 backend/riskintel.db ".tables"` shows all 10 tables.
6. `alembic stamp head` if any tables pre-existed from prior `Base.metadata.create_all` calls.

Effort: 5 min. Risk: medium (autogenerate may miss defaults). Rollback: `alembic downgrade -1`.

---

## 6. Exact test repair sequence

### 6.1 Create `backend/tests/conftest.py`

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()
```

Add `rootdir` config either here or in new `backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

Effort: 20 lines. Risk: low. Rollback: delete files.

### 6.2 `backend/tests/test_rules_engine_service.py` — add rule_registry seed fixture

Required because service is fail-closed and requires seeded registry. Add to `conftest.py`:

```python
@pytest.fixture
async def seeded_registry(db_session):
    from app.models.rule_registry import RuleRegistry
    from app.services.rule_registry_service import RuleRegistryService
    # Seed E1, E2, E5 rules with default payloads
    ...
    return RuleRegistryService(repo)
```

Effort: 30 lines. Risk: medium (engine behavior depends on payload shape). Rollback: skip this test group, mark xfail.

### 6.3 `backend/tests/test_model_registry_service.py` and `test_rule_registry_service.py`

Same fixture dependency. Same conftest addition.

Effort: shares §6.2. Risk: same.

### 6.4 `backend/tests/test_e2e_failures.py`, `test_e2e_person_a.py`, `test_e2e_person_b.py`, `test_orchestrator.py`

After §4 routes registered, these can collect. The 4 e2e tests assert 400/500 on failure paths and 200 on success — they should pass against the registered `assess_v1_router`. Verify:

```bash
cd backend && venv/Scripts/python.exe -m pytest tests/test_e2e_*.py tests/test_orchestrator.py -v
```

The `TestClient` in tests will hit `POST /api/assess*` via the registered router. `execute_orchestrator` runs in-process.

Effort: zero new test code; run only. Risk: low (tests were written for the exact orchestrator behavior we preserved). Rollback: revert §4.

### 6.5 Verify all 9 test files

```bash
cd backend && venv/Scripts/python.exe -m pytest tests/ -v
```

Expected: 15 engine tests + 4 e2e failures + n e2e success + n orchestrator + n service tests = ~30+ tests. Some service tests may still fail on fixture work; mark xfail for now.

Effort: 5 min verify. Risk: low (no test code changes, just observe).

---

## 7. Lowest-risk order of execution

Sequence chosen so each step has independent rollback and no step requires the next to be valuable.

| Step | Action | Effort | Rollback risk | Depends on |
| :---: | :--- | :--- | :--- | :--- |
| 1 | Install missing deps into venv (`pip install -r requirements.txt`) | 2 min | none | — |
| 2 | Delete `backend/nul` | 1 sec | none | — |
| 3 | Delete root-level `test_audit_fail_closed.py` and `test_ml_contract_fuzzing.py` | 1 sec | none | — |
| 4 | Fix `app/core/config.py:29` `parents[3]` → `parents[2]` | 30 sec | none | — |
| 5 | Fix `app/db/session.py:34` annotation | 30 sec | none | — |
| 6 | Fix `app/api/health.py:96` DDL for SQLite | 30 sec | none | — |
| 7 | Fix `app/audit.py:14` path depth | 1 min | low (2 audit rows) | step 4 |
| 8 | Fix `app/services/rules_engine_service.py:339` threshold unit | 1 min | low | step 1 |
| 9 | Fix `app/main.py:103-125` to wrap `RequestValidationError` in envelope | 5 min | low | — |
| 10 | Delete `backend/app/routes/assess.py` + `routes/` dir | 30 sec | none | — |
| 11 | Delete `backend/app/config.py` (Flask Config) and `backend/app/audit.py` import of it | 1 min | none | — |
| 12 | Delete `backend/run.py`, `backend/audit.py` (root RF eval), `legacy_archive/` | 30 sec | none | — |
| 13 | Delete `backend/app/middleware/` and `backend/app/report/` empty dirs | 30 sec | none | — |
| 14 | Strip PostgreSQL types in all 11 `app/models/*.py` files | 20 min | medium | step 1 |
| 15 | Generate first alembic migration + `alembic upgrade head` | 5 min | medium | step 14 |
| 16 | Add `backend/app/api/v1/assess.py` (4 routes wrapping `execute_orchestrator`) | 10 min | low | step 1 |
| 17 | Add `backend/app/api/v1/reports.py` (2 stub routes) | 5 min | none | step 1 |
| 18 | Register routers in `app/main.py:128-132` | 5 min | low | steps 16, 17 |
| 19 | Change `API_V1_PREFIX` to `/api` in `core/config.py:34` | 30 sec | low | step 18 |
| 20 | Add `backend/tests/conftest.py` + `backend/pytest.ini` | 10 min | low | step 15 |
| 21 | Run full test suite `pytest tests/ -v` | 5 min | none (observe) | steps 15-20 |
| 22 | Delete `riskintel.db` (repo root) — 2 rows, schema preserved in backend/ | 5 sec | low (audit data) | step 7 |

**Total estimated effort: ~70 minutes.**

**Cumulative rollback risk: medium** (only steps 7, 8, 9, 14, 15, 18, 19, 22 carry any risk; all independent).

---

## Stop conditions

Stop and surface to user if any of these occur during execution:

1. `alembic revision --autogenerate` produces a file referencing `uuid-ossp` or `gen_random_uuid` (means a model edit in §1.4 was missed).
2. `pytest tests/` shows the same `ModuleNotFoundError: No module named 'fastapi'` after step 1 (means venv is wrong or requirements file is wrong).
3. `execute_orchestrator` returns a different shape than the audit recorded (means some unintended import path was broken).
4. `alembic upgrade head` fails on a model that is imported but not edited in §1.4 (means an import path is missing).

End of plan.
