from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.auth import verify_api_key, verify_hmac
from api.idempotency import idempotent
from schemas.api_models import (
    IntakeRequest,
    TriageRequest,
    AAVerificationWebhook,
    FOVerificationWebhook,
    RepromptRequest,
    OptimizationRequest,
    SessionResponse,
    PaginatedApplicationList,
    ApplicationDetailResponse,
    PaginatedDeadLetterList,
    CoApplicantRequest,
    ArtifactUploadRequest
)

from services.intake import create_application, submit_application
from services.triage import run_triage_evaluation
from services.verification import process_aa_webhook, process_fo_webhook, submit_reprompt_data, submit_artifact
from services.optimization import run_optimization
from services.decision import accept_counter_offer, reject_counter_offer, submit_coapplicant
from models.session import ApplicationSession
from models.dead_letter import DeadLetterWebhook

router = APIRouter()

# Read endpoints — protected by API key
@router.get("/applications", response_model=PaginatedApplicationList, dependencies=[Depends(verify_api_key)])
def api_get_applications(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    total = db.query(ApplicationSession).count()
    items = db.query(ApplicationSession).order_by(ApplicationSession.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total, "limit": limit, "skip": skip}

from services.explanation import generate_decision_explanation

@router.get("/applications/{session_id}", response_model=ApplicationDetailResponse, dependencies=[Depends(verify_api_key)])
def api_get_application_detail(session_id: str, db: Session = Depends(get_db)):
    session_obj = db.query(ApplicationSession).filter(ApplicationSession.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Application not found")
        
    explanation = generate_decision_explanation(session_obj)
    
    response_data = {
        "id": session_obj.id,
        "current_state": session_obj.current_state,
        "loan_amount": session_obj.loan_amount,
        "loan_term": session_obj.loan_term,
        "loan_purpose": session_obj.loan_purpose,
        "income_bracket": session_obj.income_bracket,
        "bureau_gate_status": session_obj.bureau_gate_status,
        "triage_pass": session_obj.triage_pass,
        "created_at": session_obj.created_at,
        "updated_at": session_obj.updated_at,
        "explanation": explanation
    }
    return response_data

@router.get("/dlq", response_model=PaginatedDeadLetterList, dependencies=[Depends(verify_api_key)])
def api_get_dlq(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    total = db.query(DeadLetterWebhook).count()
    items = db.query(DeadLetterWebhook).order_by(DeadLetterWebhook.occurred_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total, "limit": limit, "skip": skip}

# Internal routes — protected by API key + idempotency
@router.post("/apply", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
@router.post("/applications/intake", response_model=SessionResponse, include_in_schema=False, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_create_and_submit_intake(request: IntakeRequest, db: Session = Depends(get_db)):
    session_obj = create_application(db, request.model_dump())
    updated_session = submit_application(db, session_obj.id, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/applications/{session_id}/triage", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_triage(session_id: str, request: TriageRequest, db: Session = Depends(get_db)):
    updated_session = run_triage_evaluation(db, session_id, request.bureau_status, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/applications/{session_id}/reprompt", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_reprompt(session_id: str, request: RepromptRequest, db: Session = Depends(get_db)):
    updated_session = submit_reprompt_data(db, session_id, request.secondary_contact, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/applications/{session_id}/artifact", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_submit_artifact(session_id: str, request: ArtifactUploadRequest, db: Session = Depends(get_db)):
    updated_session = submit_artifact(db, session_id, request.artifact_type, request.file_hash, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/applications/{session_id}/optimize", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_optimize(session_id: str, request: OptimizationRequest, db: Session = Depends(get_db)):
    updated_session = run_optimization(db, session_id, annual_rate=request.annual_rate, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/decision/{session_id}/accept", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_accept_counter_offer(session_id: str, db: Session = Depends(get_db)):
    updated_session = accept_counter_offer(db, session_id, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/decision/{session_id}/reject", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_reject_counter_offer(session_id: str, db: Session = Depends(get_db)):
    updated_session = reject_counter_offer(db, session_id, actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/decision/{session_id}/coapplicant", response_model=SessionResponse, dependencies=[Depends(verify_api_key), Depends(idempotent)])
def api_submit_coapplicant(session_id: str, request: CoApplicantRequest, db: Session = Depends(get_db)):
    updated_session = submit_coapplicant(db, session_id, request.model_dump(), actor="api_client")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

# Webhook routes — protected by HMAC-SHA256 + timestamp
@router.post("/webhooks/aa", response_model=SessionResponse, dependencies=[Depends(verify_hmac)])
async def api_aa_webhook(request: AAVerificationWebhook, db: Session = Depends(get_db)):
    updated_session = process_aa_webhook(db, request.session_id, request.model_dump(), actor="aa_webhook")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}

@router.post("/webhooks/fo", response_model=SessionResponse, dependencies=[Depends(verify_hmac)])
async def api_fo_webhook(request: FOVerificationWebhook, db: Session = Depends(get_db)):
    updated_session = process_fo_webhook(db, request.session_id, request.model_dump(), actor="fo_webhook")
    return {"session_id": updated_session.id, "current_state": updated_session.current_state}
