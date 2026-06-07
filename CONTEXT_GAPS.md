# RiskIntel Context Gaps

**Date:** 2026-06-07
**Purpose:** Identify every piece of information still missing that would prevent a new AI session from safely making implementation decisions. 

---

## Critical

### 1. Current API Startup State
- **Why it matters:** Known Limitations state that the production HTTP layer cannot start and fails at import, but `app/main.py` is fully fleshed out with routers. An AI session cannot safely edit or debug API endpoints if the baseline startup status (and the exact import trace) is unknown.
- **Evidence required:** Terminal execution output of `cd backend && uvicorn app.main:app`.
- **Repository location:** `backend/app/main.py` and `backend/run.py`.
- **Risk if ignored:** AI might write new features on top of a fundamentally broken or un-bootable FastAPI instance, compounding import errors.

### 2. Current Database Schema & Migration State
- **Why it matters:** There are two parallel databases (`backend/riskintel.db` vs root `riskintel.db`) with conflicting schemas. The audit log is meant to be fail-closed, but if the app is pointing to the wrong database or if migrations are broken, the audit log will fail at runtime.
- **Evidence required:** Output of `cd backend && alembic current` and schema inspections of both SQLite files.
- **Repository location:** `backend/alembic.ini`, `backend/alembic/`, `backend/riskintel.db`.
- **Risk if ignored:** Database writes (specifically the mandatory audit logging) will fail, instantly breaking the strict Model Risk Committee compliance rules.

---

## High

### 3. Current Test Pass Rate
- **Why it matters:** 15/15 engine tests supposedly passed during the audit, but the current, exact state of the test suite is unknown. An AI cannot confidently refactor the orchestrator or routing logic without a verified green baseline.
- **Evidence required:** Terminal output of `cd backend && pytest`.
- **Repository location:** `backend/tests/`.
- **Risk if ignored:** Unintentional regressions and the inability to distinguish between pre-existing bugs and AI-authored bugs.

---

## Medium

### 4. Runtime Dependency Integrity
- **Why it matters:** The environment may be missing dependencies listed in `requirements.txt` or have version conflicts, contributing to the "fails at import" limitation.
- **Evidence required:** Terminal output of `pip check` or the stack trace of a failed `uvicorn` boot.
- **Repository location:** `backend/requirements.txt`.
- **Risk if ignored:** The AI will chase ghost bugs in the code when the issue is purely environmental.

---

## Low

### 5. E4 Output Generics
- **Why it matters:** E4 generates text based on internal engine outputs. It is unclear if E4 throws exceptions when encountering `None` values or missing keys from disabled engines (like E1/E3).
- **Evidence required:** E4 specific unit tests or direct manual invocation of the E4 service function.
- **Repository location:** `backend/app/engines/` (specifically the E4 module).
- **Risk if ignored:** Minor string formatting errors or missing fields in the final output payload.
