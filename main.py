from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from api.routes import router
from api.idempotency import IdempotencyMiddleware, _IdempotencyReplayResponse

from core.fsm_graph import InvalidTransitionError
from models.dead_letter import DeadLetterWebhook
from db.session import SessionLocal
import json
import uuid

async def log_dead_letter(request: Request, failure_reason: str, error_details: str):
    """
    Saves a dead-letter log for failed webhooks. Uses a fresh DB session
    so the insert survives the main transaction's rollback.
    """
    if not request.url.path.startswith("/webhooks/"):
        return

    try:
        body_bytes = await request.body()
        raw_payload = body_bytes.decode('utf-8', errors='replace')
    except Exception:
        raw_payload = "<unreadable body>"

    session_id = None
    try:
        payload_dict = json.loads(raw_payload)
        session_id = payload_dict.get("session_id")
    except Exception:
        pass

    db = SessionLocal()
    try:
        record = DeadLetterWebhook(
            id=str(uuid.uuid4()),
            session_id=session_id,
            route=request.url.path,
            raw_payload=raw_payload,
            failure_reason=failure_reason,
            error_details=error_details
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


app = FastAPI(title="RiskIntel Orchestration API", version="2.0.0")

app.add_middleware(IdempotencyMiddleware)
app.include_router(router)

from fastapi import Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from sqlalchemy import text
from fastapi import status

@app.get("/health", tags=["Operational"])
def health_check():
    """
    Liveness probe.
    Indicates whether the process is running.
    Does not depend on external services like the database.
    """
    return {"status": "ok"}

@app.get("/ready", tags=["Operational"])
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe.
    Indicates whether the application can safely accept traffic.
    Checks database connectivity.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "details": str(e)}
        )

@app.exception_handler(InvalidTransitionError)
async def invalid_transition_exception_handler(request: Request, exc: InvalidTransitionError):
    await log_dead_letter(request, "INVALID_STATE", str(exc))
    return JSONResponse(
        status_code=409,
        content={"message": "State machine transition conflict.", "details": "The requested event is not allowed in the current state."},
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    await log_dead_letter(request, "DOMAIN_ERROR", str(exc))
    return JSONResponse(
        status_code=400,
        content={"message": "Invalid request or payload.", "details": "The submitted payload failed domain validation."},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    await log_dead_letter(request, "INVALID_PAYLOAD", str(exc))
    return JSONResponse(
        status_code=422,
        content={"message": "Validation Error", "details": exc.errors()},
    )


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(_IdempotencyReplayResponse)
async def idempotency_replay_handler(request: Request, exc: _IdempotencyReplayResponse):
    return exc.response
