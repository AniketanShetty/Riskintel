# RiskIntel V2

## 1. Project Overview

RiskIntel V2 is a deterministic, FSM-driven loan decision orchestration system. It is designed to safely sequence the evaluation of loan applicants through Intake, Triage, external Verifications (Bureau, Bank, Webhooks), and Optimization.

Unlike V1, V2 entirely removes obsolete ML models in favor of a mathematically rigorous State Machine that ensures applicants never reach invalid states and that all financial calculations are auditable.

## 2. Architecture Overview

- **Framework:** FastAPI (Python 3.13)
- **Database:** PostgreSQL via SQLAlchemy (async)
- **Migrations:** Alembic
- **Orchestration:** Finite State Machine (FSM) with robust rollback capabilities and Dead-Letter Queue logging for webhooks.
- **Idempotency:** Request deduplication built into the API layer.

The FSM transitions applicants through states like `INTAKE`, `TRIAGE`, `VERIFICATION_AA`, `VERIFICATION_FO`, `READY`, `NEARLY_READY`, and terminal states like `REJECTED` or `APPROVED`.

## 3. Local Development

To run the application locally without Docker:

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup a local Postgres database and export environment variables (see below)
# export DATABASE_URL="postgresql://user:pass@localhost:5432/riskintel"

# 4. Run Migrations
alembic upgrade head

# 5. Start the API server
uvicorn main:app --reload
```

## 4. Docker Setup

The easiest way to stand up the complete stack (PostgreSQL + RiskIntel API + Auto-migrations) is via Docker Compose.

```bash
# Build and start the stack in detached mode
docker compose up -d --build

# View logs
docker logs riskintel-backend-1 -f

# Shut down the stack
docker compose down
```

The Docker stack uses a `.dockerignore` file to ensure lightning-fast builds by omitting legacy analytics and data folders.

## 5. Environment Variables

The application enforces a **fail-fast configuration pattern**. It will refuse to start if the following required variables are missing:

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | The PostgreSQL connection string (e.g. `postgresql://postgres:postgrespassword@db:5432/riskintel`) |
| `RISKINTEL_API_KEY` | The secret key required by clients to interact with internal endpoints. |
| `RISKINTEL_WEBHOOK_SECRET` | The secret used to validate HMAC-SHA256 signatures on incoming webhooks. |

*(These are configured centrally via `pydantic-settings` in `core/config.py`).*

## 6. Running Migrations

Database schemas are version-controlled via Alembic.

To apply migrations up to the latest head:
```bash
alembic upgrade head
```

To create a new migration after modifying an ORM model:
```bash
alembic revision --autogenerate -m "description_of_change"
```

## 7. Running Tests

RiskIntel V2 includes a comprehensive test suite (Unit, FSM State-Graph, and End-to-End). Ensure your local test database is accessible.

```bash
# Run the entire suite
pytest tests/ -v

# Run specific E2E validations
pytest tests/test_e2e_system.py -v
```

## 8. Authentication

All internal API endpoints require API Key authentication.
Provide the key via the `X-API-Key` HTTP Header.

```http
GET /health HTTP/1.1
X-API-Key: your_secret_api_key
```

## 9. Webhook Security

External integrations communicating with RiskIntel via webhooks must secure their payload. Webhooks are authenticated via HMAC-SHA256 signatures over the raw payload bytes and a timestamp to prevent replay attacks.

**Headers Required:**
- `X-Webhook-Timestamp`: Unix timestamp (e.g., `1718000000`)
- `X-Webhook-Signature`: HMAC SHA256 hex signature.

The signature is generated using the `RISKINTEL_WEBHOOK_SECRET`. 
*Payload to sign:* `timestamp_string + "." + raw_body_bytes`.

## 10. API Endpoints

### Core Workflows
- `POST /apply`: Intake a new applicant.
- `POST /triage`: Run triage math and routing.
- `POST /optimize`: Evaluate optimization logic.

### Webhooks
- `POST /webhook/aa`: Receive Account Aggregator data.
- `POST /webhook/fo`: Receive Field Officer verification data.

### Decision Actions
- `POST /decision/{session_id}/accept`: Accept a counter-offer.
- `POST /decision/{session_id}/reject`: Reject a counter-offer.
- `POST /decision/{session_id}/coapplicant`: Submit a co-applicant to repair a thin file.

### Operational Probes
- `GET /health`: Liveness probe (Process is running).
- `GET /ready`: Readiness probe (Database is reachable).

## 11. Recovery Flows

RiskIntel V2 supports state-orchestrated recovery loops to prevent silent rejections:

1. **Reprompt Loop:** If Field Officer (FO) data is missing critical fields or is blurry, the system drops the applicant into the `FO_REPROMPT` state, halting progression until a valid payload arrives.
2. **Counter-Offers:** If the applicant's requested loan exceeds capacity, the system proposes a mathematically optimized counter-offer (`NEARLY_READY`). The user can explicitly `/accept` or `/reject`.
3. **Co-Applicant Injection:** If an applicant is `REJECTED` strictly due to thin credit, they may be offered the chance to submit a co-applicant via the `/coapplicant` endpoint, resetting their FSM progression.

## 12. Troubleshooting

- **Server fails to start with Pydantic errors:** Ensure `DATABASE_URL`, `RISKINTEL_API_KEY`, and `RISKINTEL_WEBHOOK_SECRET` are defined in your environment.
- **Docker build takes forever:** Ensure you haven't deleted the `.dockerignore` file. Legacy datasets in `/data` and models in `/backend` are intentionally ignored.
- **Webhooks fail silently:** Check the `dead_letter_webhooks` table in Postgres. All invalid payload or out-of-state webhooks are durably logged here even if the main business transaction rolls back.
- **API returns 503 Service Unavailable:** The `/ready` probe will return 503 if the database is down. Check PostgreSQL connectivity.
