"""
Assessor endpoint — exposes the existing orchestrator over HTTP.

Wraps `app.orchestrator.execute_orchestrator` without modifying any
business logic. The orchestrator handles validation, routing, engine
execution, audit logging, and response assembly.

Error envelope (frozen per docs/output_contracts.md §5):
    {"status": "error", "error": {"code": "...", "message": "...", "details": [...]}}

Endpoints (mounted under /api):
    POST /api/assess            — unified gateway (user_type inferred or echoed)
    POST /api/assess/person-a   — forces user_type=person_a
    POST /api/assess/person-b   — forces user_type=person_b
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Union, Annotated

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field

from app.schemas.requests import PersonARequest, PersonBRequest, UnifiedRequest
from app.schemas.responses import PersonAResponse, PersonBResponse

UnifiedResponse = Annotated[Union[PersonAResponse, PersonBResponse], Field(discriminator='user_type')]

from app.audit import write_audit_record  # noqa: F401  (re-exported for tests/patches)
from app.exceptions import (
    AuditLogError,
    CriticalEngineError,
    NonCriticalEngineError,
    RequestValidationError,
)
from app.orchestrator import execute_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assess"])


def _error(status_code: int, code: str, message: str, details: Optional[list] = None) -> JSONResponse:
    """Build the frozen contract error envelope as a JSONResponse.

    Top-level shape is the contract envelope; `details` is forwarded as-is
    so engine-diagnostic dicts (engine, error_type, context) and per-field
    validation records both pass through without a strict schema mismatch.
    """
    payload: Dict[str, Any] = {"status": "error", "error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def _run(payload: Dict[str, Any]):
    """Run orchestrator and translate domain exceptions to the frozen envelope."""
    try:
        return execute_orchestrator(payload)
    except RequestValidationError as exc:
        return _error(
            status_code=400,
            code="VALIDATION_ERROR",
            message=str(exc),
            details=exc.details,
        )
    except CriticalEngineError as exc:
        logger.error("Critical engine failure: %s", exc)
        return _error(
            status_code=500,
            code="ENGINE_FAILURE",
            message=f"A critical engine failed: {exc.engine_name}",
            details=[
                {
                    "engine": exc.engine_name,
                    "error_type": type(exc.original_exception).__name__,
                    "context": str(exc.original_exception),
                }
            ],
        )
    except NonCriticalEngineError as exc:
        logger.warning("Non-critical engine failure: %s", exc)
        return _error(
            status_code=500,
            code="ENGINE_FAILURE",
            message=f"Non-critical engine failed: {exc.engine_name}",
        )
    except AuditLogError as exc:
        logger.error("Audit commit failure (fail-closed): %s", exc)
        return _error(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Fail-closed policy active: audit trail commit failed. Underwriting decision withheld.",
        )


@router.post("/assess", response_model=UnifiedResponse)
async def assess_unified(payload: UnifiedRequest):
    """Unified gateway. user_type may be supplied in the payload."""
    return _run(payload.model_dump())


@router.post("/assess/person-a", response_model=PersonAResponse)
async def assess_person_a(payload: PersonARequest):
    """Person A pipeline endpoint. Forces user_type=person_a."""
    return _run(payload.model_dump())


@router.post("/assess/person-b", response_model=PersonBResponse)
async def assess_person_b(payload: PersonBRequest):
    """Person B pipeline endpoint. Forces user_type=person_b."""
    return _run(payload.model_dump())
