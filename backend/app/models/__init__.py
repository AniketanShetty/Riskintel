"""RiskIntel ORM models — import all to register with metadata."""
from app.models.applicant import Applicant
from app.models.assessment import Assessment
from app.models.rule_registry import RuleRegistry
from app.models.model_registry import ModelRegistry
from app.models.archetype_result import ArchetypeResult
from app.models.recommendation_result import RecommendationResult
from app.models.eligibility_result import EligibilityResult
from app.models.risk_tier_result import RiskTierResult
from app.models.readiness_result import ReadinessResult
from app.models.audit_log import AuditLog

__all__ = [
    "Applicant",
    "Assessment",
    "RuleRegistry",
    "ModelRegistry",
    "ArchetypeResult",
    "RecommendationResult",
    "EligibilityResult",
    "RiskTierResult",
    "ReadinessResult",
    "AuditLog",
]
