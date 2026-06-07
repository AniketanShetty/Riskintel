import logging
import uuid
import time
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Assuming local imports match the previously generated schemas and models
from schemas import (
    AssessmentRequest, AssessmentResponse, AssessmentStatus, DecisionSummary,
    AuditMetadata, LineageMetadata, AuditEvent
)
from rule_engine import E1EligibilityEngine, RuleConfiguration, EvaluationInput

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("riskintel_orchestrator")

# --- Mock Dependencies (Database, HTTP Clients, Audit Brokers) ---
class DatabaseSession:
    """Mock async DB session to demonstrate transaction boundaries."""
    async def begin(self): pass
    async def commit(self): pass
    async def rollback(self): pass
    async def add(self, obj): pass

async def get_db_session() -> DatabaseSession:
    yield DatabaseSession()

class KafkaAuditPublisher:
    """Mock async Kafka producer for fail-closed audit logging."""
    async def publish(self, event: AuditEvent):
        # Simulating a potential network partition timeout here
        pass

async def get_audit_publisher() -> KafkaAuditPublisher:
    yield KafkaAuditPublisher()


class MLInferenceClient:
    """Mock async HTTP client for communicating with E3/E4 Inference Service."""
    async def predict_e3(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"model_id": "m-883a-kmns-v2.1", "archetype_label": "Mid-Career Established"}

    async def predict_e4(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"model_id": "m-994b-recs-v1.8", "suggested_limit": 125000.00, "improvement_actions": ["Maintain low utilization."]}

async def get_ml_client() -> MLInferenceClient:
    yield MLInferenceClient()


# --- Service Layer ---
class AssessmentOrchestratorService:
    def __init__(
        self,
        db: DatabaseSession = Depends(get_db_session),
        audit_publisher: KafkaAuditPublisher = Depends(get_audit_publisher),
        ml_client: MLInferenceClient = Depends(get_ml_client)
    ):
        self.db = db
        self.audit = audit_publisher
        self.ml = ml_client

        # Initialize E1 Engine with mocked active rule configuration
        config = RuleConfiguration(
            engine_id="E1",
            rule_name="Standard Eligibility",
            version="v1.0.2",
            logic_payload={"cibil_min": 650}
        )
        self.e1_engine = E1EligibilityEngine(config)

    async def process_assessment(self, request_payload: AssessmentRequest, correlation_id: uuid.UUID) -> AssessmentResponse:
        start_time_ns = time.perf_counter_ns()
        assessment_id = uuid.uuid4()
        
        logger.info(f"[{correlation_id}] Starting assessment {assessment_id}")

        await self.db.begin()
        try:
            # 1. Create Assessment Record (Mocked)
            # await self.db.add(Assessment(id=assessment_id, input_features=request_payload.model_dump()))

            # 2. Execute E1 Rules Engine
            e1_input = EvaluationInput(
                assessment_id=assessment_id,
                cibil_score=request_payload.financial_features.cibil_score
            )
            e1_result = self.e1_engine.evaluate(e1_input)

            lineage = LineageMetadata(
                e1_rule_version=e1_result.rule_version,
                e2_rule_version=None,
                e3_model_id=None,
                e4_model_id=None,
                e5_rule_version=None
            )

            # 3. Handle E1 Rejection (Fail Fast)
            if not e1_result.is_eligible:
                logger.info(f"[{correlation_id}] Assessment {assessment_id} REJECTED by E1.")
                
                # Write Audit
                audit_event = AuditEvent(
                    correlation_id=correlation_id,
                    assessment_id=assessment_id,
                    engine_id="E1",
                    event_type="E1_REJECTION",
                    payload={"rejection_reason": e1_result.rejection_reason}
                )
                await self.audit.publish(audit_event)
                await self.db.commit()

                execution_time_ms = (time.perf_counter_ns() - start_time_ns) // 1_000_000

                return AssessmentResponse(
                    assessment_id=assessment_id,
                    status=AssessmentStatus.REJECTED,
                    rejection_reason=e1_result.rejection_reason,
                    decision_summary=DecisionSummary(eligibility="FAIL"),
                    audit_metadata=AuditMetadata(correlation_id=correlation_id, execution_time_ms=execution_time_ms),
                    lineage_metadata=lineage
                )

            # 4. If Approved by E1 -> Execute ML Inference (E3 & E4)
            logger.info(f"[{correlation_id}] E1 Passed. Executing ML Inference.")
            features_dict = request_payload.financial_features.model_dump()
            
            e3_output = await self.ml.predict_e3(features_dict)
            e4_output = await self.ml.predict_e4(features_dict)

            # Update Lineage
            lineage.e3_model_id = e3_output["model_id"]
            lineage.e4_model_id = e4_output["model_id"]

            # 5. Write Final Audit
            audit_event = AuditEvent(
                correlation_id=correlation_id,
                assessment_id=assessment_id,
                engine_id="DAG",
                event_type="ASSESSMENT_COMPLETED",
                payload={"archetype": e3_output["archetype_label"]}
            )
            await self.audit.publish(audit_event)
            await self.db.commit()

            execution_time_ms = (time.perf_counter_ns() - start_time_ns) // 1_000_000

            # 6. Return Approval Response
            return AssessmentResponse(
                assessment_id=assessment_id,
                status=AssessmentStatus.APPROVED,
                decision_summary=DecisionSummary(
                    eligibility="PASS",
                    risk_tier="P2",  # Hardcoded for example, would be E2 output
                    archetype=e3_output["archetype_label"],
                    credit_limit=e4_output["suggested_limit"],
                    readiness="READY"
                ),
                improvement_actions=e4_output.get("improvement_actions", []),
                audit_metadata=AuditMetadata(correlation_id=correlation_id, execution_time_ms=execution_time_ms),
                lineage_metadata=lineage
            )

        except Exception as e:
            # FATAL: Rollback Transaction to guarantee Fail-Closed
            logger.exception(f"[{correlation_id}] Orchestrator DAG failed. Rolling back transaction.")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System timeout. No underwriting decision was made. Please try again."
            )


# --- API Routing ---
app = FastAPI(title="RiskIntel Orchestrator Service")

@app.post("/v1/assess", response_model=AssessmentResponse)
async def assess_applicant(
    payload: AssessmentRequest,
    request: Request,
    service: AssessmentOrchestratorService = Depends()
):
    correlation_id_str = request.headers.get("X-Correlation-ID")
    correlation_id = uuid.UUID(correlation_id_str) if correlation_id_str else uuid.uuid4()
    
    return await service.process_assessment(payload, correlation_id)
