# REPOSITORY REALITY AUDIT (V1)

**Date of Audit:** 2026-06-10
**Audit Methodology:** Direct inspection of Python source code and execution environments. No historical markdown files were consulted.

## 1. Backend Framework
The active backend framework is **FastAPI**, not Flask. 
There is zero trace of Flask anywhere in the `backend/app` directory. The application factory in `backend/app/main.py` explicitly instantiates a `FastAPI` app. The `backend/run.py` script starts the server using `uvicorn.run("app.main:app")`.

## 2. Boot Capability
The backend is completely functional and **boots successfully**. 
Executing `python -c "from app.main import app"` inside the backend directory completes without any missing dependency errors. 

## 3. Database State
The application uses SQLite, but it specifically targets `backend/riskintel.db`.
The `config.py` explicitly defines the database path as exactly three parent directories above `backend/app/core/config.py`, resulting in `backend/riskintel.db`. The `riskintel.db` at the root of the repository is abandoned (0 bytes), while `backend/riskintel.db` is an active 7.4 MB database.

## 4. Engine Execution
The `orchestrator.py` file is the central execution graph. By reading its source code, it actively imports and executes the following engines:
* **E1 (Eligibility ML):** Active via `get_eligibility(payload)`
* **E2 (Risk Tier):** Active via `get_risk_tier(cibil_val)`
* **E3 (Archetype):** Active via `get_borrower_archetype(payload)`
* **E4 (Recommendation):** Active via `generate_person_a_recommendations` and `generate_person_b_recommendations`
* **E5 (Readiness):** Active via `get_readiness_score(payload)`
* **Livelihood Mapper:** Active via `map_livelihood(primary_biz)`

None of the mathematical engines are disabled or "mocked" in the primary pipeline.

## 5. Architectural Verdict
The concept of a "Dual-Architecture State" (a working Legacy Flask app vs a broken FastAPI app) was an AI hallucination documented in previous markdown files.

**The repository contains exactly one functional backend, and it is built entirely on FastAPI.**
