from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid
import time
from datetime import datetime, timezone


@dataclass(frozen=True)
class RuleConfiguration:
    """Represents the versioned configuration loaded from the rule_registry database."""
    engine_id: str
    rule_name: str
    version: str
    logic_payload: Dict[str, Any]


@dataclass(frozen=True)
class EvaluationInput:
    """Strictly typed input required for E1 Evaluation."""
    assessment_id: uuid.UUID
    cibil_score: int


@dataclass(frozen=True)
class EvaluationResult:
    """The immutable result of an E1 evaluation, ready for audit and orchestration."""
    assessment_id: uuid.UUID
    is_eligible: bool
    rejection_reason: Optional[str]
    rule_version: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_ms: int = 0


class E1EligibilityEngine:
    """
    Deterministic Rules Engine replacing the deprecated Random Forest model.
    Evaluates applicant eligibility based on a configurable CIBIL score threshold.
    """

    def __init__(self, config: RuleConfiguration):
        if config.engine_id != "E1":
            raise ValueError(f"Expected engine_id 'E1', got '{config.engine_id}'")
        
        self.config = config
        # Extract the specific threshold from the JSONB logic payload
        self.cibil_threshold = self.config.logic_payload.get("cibil_min")
        
        if not isinstance(self.cibil_threshold, int):
            raise TypeError("E1 logic_payload must contain integer 'cibil_min'")

    def evaluate(self, payload: EvaluationInput) -> EvaluationResult:
        """
        Executes the E1 eligibility rule against the provided applicant payload.
        """
        start_time = time.perf_counter_ns()
        
        is_eligible = payload.cibil_score >= self.cibil_threshold
        
        rejection_reason = None
        if not is_eligible:
            rejection_reason = (
                f"Applicant credit score ({payload.cibil_score}) is below "
                f"the minimum required threshold ({self.cibil_threshold})."
            )

        execution_time_ms = (time.perf_counter_ns() - start_time) // 1_000_000

        return EvaluationResult(
            assessment_id=payload.assessment_id,
            is_eligible=is_eligible,
            rejection_reason=rejection_reason,
            rule_version=self.config.version,
            execution_time_ms=execution_time_ms
        )
