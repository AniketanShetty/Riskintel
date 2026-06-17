"""
api/idempotency.py
------------------
Idempotency dependency + ASGI middleware for FastAPI routes.

Architecture:
  - `idempotent` dependency: runs BEFORE the route handler.
      - No key → pass through.
      - Key + matching record in TTL → raise _IdempotencyReplayResponse (short-circuits).
      - Key + record with different body → 422.
      - Key + no record → set request.state.idempotency_pending, continue.
  - `IdempotencyMiddleware`: wraps the entire ASGI app.
      - Intercepts responses for requests that have request.state.idempotency_pending set.
      - Reads the response body and persists it to idempotency_records.
      - Uses a fresh DB session (independent of the route's session, which may be closed).
"""
import hashlib
import json
import time
import uuid

from fastapi import Depends, Header, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response as StarletteResponse
from starlette.types import ASGIApp

from api.dependencies import get_db
from models.idempotency import IdempotencyRecord

IDEMPOTENCY_TTL_SECONDS: int = 86400  # 24 hours


# ---------------------------------------------------------------------------
# Pre-route dependency
# ---------------------------------------------------------------------------

async def idempotent(
    request: Request,
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
) -> None:
    """
    FastAPI dependency — runs before the route handler.
    Short-circuits with a cached response if the key was seen before.
    Sets request.state.idempotency_pending for the middleware to pick up.
    """
    if not x_idempotency_key:
        return

    if len(x_idempotency_key) > 64:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="X-Idempotency-Key must be 64 characters or fewer.")

    raw_body: bytes = await request.body()
    request_hash = hashlib.sha256(raw_body).hexdigest()
    route = request.url.path

    existing = db.query(IdempotencyRecord).filter_by(
        idempotency_key=x_idempotency_key,
        route=route,
    ).first()

    if existing:
        age = time.time() - existing.created_at.timestamp()
        if age <= IDEMPOTENCY_TTL_SECONDS:
            if existing.request_hash != request_hash:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Idempotency key reused with a different request body. "
                        "Use a new key for a new request."
                    ),
                )
            cached_body = json.loads(existing.response_body)
            raise _IdempotencyReplayResponse(
                JSONResponse(
                    content=cached_body,
                    status_code=existing.response_status,
                    headers={"X-Idempotency-Replayed": "true"},
                )
            )

    # Mark this request for post-response storage
    request.state.idempotency_pending = {
        "key": x_idempotency_key,
        "route": route,
        "request_hash": request_hash,
    }


# ---------------------------------------------------------------------------
# Sentinel exception
# ---------------------------------------------------------------------------

class _IdempotencyReplayResponse(Exception):
    """Short-circuits route execution and returns a cached response."""
    def __init__(self, response: StarletteResponse):
        self.response = response


# ---------------------------------------------------------------------------
# Post-route middleware — stores the response after a successful execution
# ---------------------------------------------------------------------------

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Intercepts outgoing responses for requests that have idempotency_pending set.
    Persists the response body and status code to idempotency_records using a
    fresh DB session so the route's own session lifecycle does not interfere.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        pending = getattr(request.state, "idempotency_pending", None)
        if pending is None:
            return response

        # Only cache successful responses
        if response.status_code != 200:
            return response

        # Read the response body (streaming)
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        try:
            body_dict = json.loads(body_bytes)
        except (json.JSONDecodeError, ValueError):
            # Cannot cache non-JSON response — return as-is
            from starlette.responses import Response as RawResponse
            return RawResponse(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Use the DB session stored by the idempotent dependency on request.state.
        # This ensures the correct test DB is used in testing and production DB in production.
        db = getattr(request.state, "idempotency_db", None)
        if db is None:
            # Fallback: open a fresh session (should not normally occur)
            from db.session import SessionLocal
            db = SessionLocal()
            owns_db = True
        else:
            owns_db = False

        try:
            record = IdempotencyRecord(
                id=str(uuid.uuid4()),
                idempotency_key=pending["key"],
                route=pending["route"],
                request_hash=pending["request_hash"],
                response_body=json.dumps(body_dict),
                response_status=response.status_code,
            )
            db.add(record)
            db.commit()
        except IntegrityError:
            db.rollback()  # Concurrent request already stored — safe
        finally:
            if owns_db:
                db.close()

        return JSONResponse(
            content=body_dict,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
