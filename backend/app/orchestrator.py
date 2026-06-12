"""
orchestrator.py

Central Orchestration Layer for the RiskIntel API.
Handles request validation, pipeline routing, engine execution ordering,
exception isolation, conflict resolution, audit logging, and response assembly.
"""
import uuid
import time
import copy
import hashlib
import json
import logging
import math
from typing import Dict, Any, Tuple

# Exceptions
from app.exceptions import (
    CriticalEngineError,
    NonCriticalEngineError,
    RequestValidationError,
    AuditLogError,
    GovernanceError,
)

# Lineage and Audit
from app.lineage import get_model_lineage_bind
from app.audit import write_audit_record

# Routing
from app.routing import route_pipeline

# Engines
from app.engines.eligibility.eligibility_engine import get_eligibility
from app.engines.risk_tier.risk_tier_engine import get_risk_tier
from app.engines.archetype.borrower_archetype_engine import get_borrower_archetype
from app.engines.readiness.readiness_engine import get_readiness_score
from app.engines.livelihood.livelihood_mapper import map_livelihood
from app.engines.recommendation.recommendation_engine import (
    generate_person_a_recommendations,
    generate_person_b_recommendations
)

logger = logging.getLogger(__name__)

# Constants for versions
API_VERSION = "v1"
REQUEST_SCHEMA_VERSION = "1.0"
DECISION_VERSION = "1.2"
RECOMMENDATION_VERSION = "1.1"

def calculate_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes a stable SHA256 hash of the request payload."""
    canonical_json = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()



def execute_orchestrator(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the RiskIntel orchestration layer.
    
    1. Validation
    2. Routing (including NTC conversion)
    3. Pipeline execution (exception isolation + defaults)
    4. Conflict resolution overrides
    5. strict Audit logging
    6. Response assembly
    """
    correlation_id = str(uuid.uuid4())
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Calculate payload hash before any routing/mutation
    request_payload_hash = calculate_payload_hash(raw_payload)
    
    # 1. Validation has moved to Pydantic models at API boundary.
    
    # 2. Pipeline Routing
    routed_user_type, payload, routing_flags, routing_decision = route_pipeline(raw_payload)
    
    # Tracks execution status of each engine
    engine_statuses = {}
    policy_override_flags = list(routing_flags)
    triggered_rule_ids = []
    
    # 3. Execution & 4. Conflict Resolution
    if routed_user_type == "person_a":
        # --- PERSON A PIPELINE ---
        # 1. Eligibility (Critical)
        try:
            eligibility_res = get_eligibility(payload)
            # Freeze-blocker fix F5: instead of raising on probability
            # decomposition drift (which crashed the response with HTTP 500
            # for realistic inputs like 50L loan on 3L income), log the
            # drift as a warning, mark the engine as drift_degraded in the
            # audit log, and continue. The verdict and recommendation
            # proceed with the engine's raw output. Drift is captured in
            # the audit log for offline review.
            invariant_drift = abs(
                eligibility_res["bias"]
                + sum(eligibility_res["feature_contributions"].values())
                - eligibility_res["probability"]
            )
            if invariant_drift > 1e-3:
                logger.warning(
                    "E1 probability decomposition drift %.6f > 1e-3; degrading",
                    invariant_drift,
                )
                engine_statuses["E1"] = "drift_degraded"
            else:
                engine_statuses["E1"] = "success"
        except Exception as e:
            logger.error(f"E1 Eligibility Engine failure: {e}")
            engine_statuses["E1"] = "failed"
            raise CriticalEngineError("E1", e)
            
        # 2. Risk Tier (Critical)
        try:
            cibil_val = int(payload.get("cibil_score"))
            risk_tier_raw = get_risk_tier(cibil_val)
            engine_statuses["E2"] = "success"
        except Exception as e:
            logger.error(f"E2 Risk Tier Engine failure: {e}")
            engine_statuses["E2"] = "failed"
            raise CriticalEngineError("E2", e)
            
        # 3. Borrower Archetype (Non-Critical)
        try:
            archetype_raw = get_borrower_archetype(payload)
            engine_statuses["E3"] = "success"
            
            # Map description based on archetype label
            label = archetype_raw.get("archetype_label", "Unknown Archetype")
            desc_map = {
                "Highly Tenured Veterans": "High tenure, older age profile with stable employment.",
                "Educated Professionals": "Higher education levels with professional background.",
                "Young Starters": "Younger demographic, lower employment tenure, early career stage.",
                "Mid-Career Established": "Moderate age, stable income, mid-career stage profile."
            }
            archetype_res = {
                "label": label,
                "cluster_id": archetype_raw.get("cluster_id", -1),
                "description": desc_map.get(label, "Represents a distinct borrower profile based on demographic clustering.")
            }
        except Exception as e:
            logger.warning(f"E3 Borrower Archetype Engine failure (Non-Critical, degrading): {e}")
            engine_statuses["E3"] = "failed_degraded"
            # Fallback
            archetype_res = {
                "label": "Unclassified",
                "cluster_id": -1,
                "description": "Unclassified profile due to engine degradation."
            }
            
        # --- Deterministic Banking Guardrails ---
        is_override = False
        eligibility_verdict = eligibility_res["verdict"]

        try:
            g_age = int(payload.get("age", 0))
            g_term = int(payload.get("loan_term", 0))
            g_income = float(payload.get("annual_income", 0))
            g_loan = float(payload.get("loan_amount", 0))
        except (ValueError, TypeError):
            g_age, g_term, g_income, g_loan = 0, 0, 0.0, 0.0
            
        maturity_age = g_age + g_term
        lti = g_loan / max(g_income, 1.0)
        
        # Guardrail 1: Low Income Review Flag
        if g_income < 300000:
            policy_override_flags.append("FLAG_LOW_INCOME_REVIEW")

        # Guardrail 2: Extreme LTI Rejection
        if lti > 6.0:
            eligibility_verdict = "Unlikely"
            is_override = True
            policy_override_flags.append("OVERRIDE_LTI_REJECTION")
            
        # Guardrail 3: Age-Term Maturity Rejection
        if maturity_age > 70:
            eligibility_verdict = "Unlikely"
            is_override = True
            policy_override_flags.append("OVERRIDE_AGE_TERM_REJECTION")

        # --- E2 overriding E1 when risk tier = P4 ---
        # Force final verdict to Unlikely if Risk Tier is P4 and E1 gave approval
        if risk_tier_raw.get("risk_tier") == "P4" and eligibility_verdict in ("Highly Likely", "Likely"):
            eligibility_verdict = "Unlikely"
            is_override = True
            policy_override_flags.append("OVERRIDE_E2_P4_REJECTION")
            
        # Also check engine level policy overrides
        if eligibility_res.get("policy_override_applied") or risk_tier_raw.get("policy_override_applied"):
            policy_override_flags.append("ENGINE_POLICY_OVERRIDE")
            
        final_verdict = eligibility_verdict
        
        # Assemble internal inputs for recommendations
        elig_copy = copy.deepcopy(eligibility_res)
        elig_copy["verdict"] = final_verdict
        elig_copy["policy_override_flags"] = policy_override_flags
        elig_copy["maturity_age"] = maturity_age
        elig_copy["lti"] = lti
        
        # Fail-loud governance: the engine contract requires a `thresholds`
        # block. If missing, raise GovernanceError instead of silently
        # substituting hardcoded values (which would reintroduce SSOT drift).
        if "thresholds" not in risk_tier_raw or not isinstance(risk_tier_raw.get("thresholds"), dict):
            raise GovernanceError(
                "RiskTierEngine did not return a `thresholds` block; "
                "cannot derive governance-bound display strings or threshold_values.",
                governance_key="risk_tier.thresholds",
            )

        risk_tier_res = {
            "tier": risk_tier_raw["risk_tier"],
            "label": {
                "P1": "Low Risk",
                "P2": "Moderate Risk",
                "P3": "Elevated Risk",
                "P4": "High Risk"
            }.get(risk_tier_raw["risk_tier"], "Unknown Risk"),
            "description": risk_tier_raw["tier_description"],
            "score_used": cibil_val,
            # Engine-provided SSOT block; fail-loud if missing.
            "thresholds": risk_tier_raw["thresholds"],
        }
        # Display strings (frozen API contract shape) — derived from the
        # engine-provided SSOT block, no hardcoded copies anywhere else.
        rt = risk_tier_res["thresholds"]
        risk_tier_res["thresholds"] = {
            "P1": f"≥ {rt['p1_min']}",
            "P2": f"{rt['p2_min']} – {rt['p2_max']}",
            "P3": f"{rt['p3_min']} – {rt['p3_max']}",
            "P4": f"≤ {rt['p4_max']}",
        }
        # Engine-provided SSOT numeric thresholds (governance refactor).
        risk_tier_res["threshold_values"] = {
            "p1_min": int(rt["p1_min"]),
            "p2_min": int(rt["p2_min"]),
            "p2_max": int(rt["p2_max"]),
            "p3_min": int(rt["p3_min"]),
            "p3_max": int(rt["p3_max"]),
            "p4_max": int(rt["p4_max"]),
        }
        
        # 4. Recommendation Engine (Non-Critical)
        try:
            recommendations_raw = generate_person_a_recommendations(
                payload, elig_copy, risk_tier_res, archetype_res
            )
            engine_statuses["E4"] = "success"
            
            # Extract and separate triggered_rule_ids so they do not leak into response
            triggered_rule_ids = recommendations_raw.pop("triggered_rule_ids", [])
            recommendations_res = recommendations_raw
        except Exception as e:
            logger.warning(f"E4 Recommendation Engine failure (Non-Critical, degrading): {e}")
            engine_statuses["E4"] = "failed_degraded"
            # Fallback
            recommendations_res = {
                "decision_verdict": final_verdict,
                "primary_reason": "Profile analysis completed under degraded mode.",
                "contributing_factors": []
            }
            
        # Assemble response payload
        # ML invariant (frozen per docs/output_contracts.md §1):
        #   bias + Σ(feature_contributions) = probability
        _bias = eligibility_res["bias"]
        _prob = eligibility_res["probability"]
        _contrib_sum = sum(eligibility_res["feature_contributions"].values())
        if abs((_bias + _contrib_sum) - _prob) > 1e-3:
            logger.warning(
                "ML invariant drift: bias(%s) + sum(%s) = %s, probability=%s (delta=%s)",
                _bias, _contrib_sum, _bias + _contrib_sum, _prob,
                (_bias + _contrib_sum) - _prob,
            )

        response = {
            "status": "success",
            "user_type": "person_a",
            "timestamp": timestamp,
            "correlation_id": correlation_id,
            "routing_decision": routing_decision,
            "applicant": payload,
            "eligibility": {
                "verdict": final_verdict,
                "probability": _prob,
                "bias": _bias,
                "feature_contributions": eligibility_res["feature_contributions"],
                "policy_override_applied": is_override or bool(eligibility_res.get("policy_override_applied")) or bool(risk_tier_raw.get("policy_override_applied"))
            },
            "risk_tier": risk_tier_res,
            "archetype": archetype_res,
            "explanation": recommendations_res
        }
        
    else:
        # --- PERSON B PIPELINE ---
        # 1. Readiness Engine (Critical)
        try:
            readiness_res = get_readiness_score(payload)
            engine_statuses["E5"] = "success"
        except Exception as e:
            logger.error(f"E5 Readiness Engine failure: {e}")
            engine_statuses["E5"] = "failed"
            raise CriticalEngineError("E5", e)
            
        # 2. Livelihood Mapper (Non-Critical)
        try:
            primary_biz = payload.get("primary_business", "Services")
            livelihood_raw = map_livelihood(primary_biz)
            engine_statuses["Livelihood Mapper"] = "success"
            livelihood_res = livelihood_raw
        except Exception as e:
            logger.warning(f"Livelihood Mapper failure (Non-Critical, degrading): {e}")
            engine_statuses["Livelihood Mapper"] = "failed_degraded"
            # Fallback
            livelihood_res = {
                "label": "General Micro-Enterprise",
                "description": "Unclassified or general small-scale business activity.",
                "cluster_id": 0
            }
            
        # --- PERSON B GUARDRAILS (Overrides and Score Caps) ---
        annual_income = float(payload.get("annual_income", 0) or 0)
        loan_amount = float(payload.get("loan_amount", 0) or 0)
        lti = loan_amount / max(annual_income, 1.0)
        
        purpose_alignment = (
            readiness_res.get("components", {})
            .get("business_viability", {})
            .get("factors", {})
            .get("purpose_alignment", "Neutral")
        )

        is_floor_breach = readiness_res.get("policy_override_applied") or readiness_res.get("floor_breach_triggered") or False
        
        # Silent Warning Flag: Low Income Review
        if annual_income < 300000:
            policy_override_flags.append("FLAG_LOW_INCOME_REVIEW")

        # Mutating Precedence Hierarchy
        if is_floor_breach:
            readiness_res["band"] = "Not Ready"
            readiness_res["score"] = 0
            policy_override_flags.append("OVERRIDE_E5_FLOOR_BREACH")
            policy_override_flags.append("ENGINE_POLICY_OVERRIDE")
        elif lti > 3.0:
            readiness_res["band"] = "Not Ready"
            readiness_res["score"] = 0
            policy_override_flags.append("OVERRIDE_EXTREME_DEBT")
        elif purpose_alignment == "Misaligned":
            readiness_res["score"] = min(readiness_res.get("score", 0), 74)
            if readiness_res.get("band") == "Ready":
                readiness_res["band"] = "Moderately Ready"
            policy_override_flags.append("FLAG_PURPOSE_MISMATCH")
            
        final_verdict = readiness_res["band"]

        # Fail-loud governance: the readiness engine contract requires a
        # `thresholds` block. If missing, raise GovernanceError instead of
        # silently substituting hardcoded values.
        if "thresholds" not in readiness_res or not isinstance(readiness_res.get("thresholds"), dict):
            raise GovernanceError(
                "ReadinessEngine did not return a `thresholds` block; "
                "cannot surface governance-bound e5_thresholds metadata.",
                governance_key="readiness.thresholds",
            )

        # Prepare readiness copy for E4
        readiness_copy = copy.deepcopy(readiness_res)
        readiness_copy["band"] = final_verdict
        readiness_copy["policy_override_flags"] = policy_override_flags
        
        # 3. Recommendation Engine (Non-Critical)
        try:
            recommendations_raw = generate_person_b_recommendations(
                payload, readiness_copy, livelihood_res
            )
            engine_statuses["E4"] = "success"
            
            triggered_rule_ids = recommendations_raw.pop("triggered_rule_ids", [])
            recommendations_res = recommendations_raw
        except Exception as e:
            logger.warning(f"E4 Recommendation Engine failure (Non-Critical, degrading): {e}")
            engine_statuses["E4"] = "failed_degraded"
            # Fallback
            recommendations_res = {
                "decision_verdict": final_verdict,
                "primary_reason": "Readiness assessment completed under degraded mode.",
                "contributing_factors": []
            }
            
        # Assemble response payload
        e5_metadata = {
            "imputed_fields": readiness_res.get("imputed_fields", []),
            "mapped_features": readiness_res.get("mapped_features", {}),
            "policy_override_applied": bool(readiness_res.get("policy_override_applied", False)),
            # Engine-provided SSOT thresholds (additive). Consumer rules read
            # `e5_thresholds.strong_status_min` etc. from this metadata.
            "e5_thresholds": readiness_res.get("thresholds", {}),
        }
        response = {
            "status": "success",
            "user_type": "person_b",
            "timestamp": timestamp,
            "correlation_id": correlation_id,
            "routing_decision": routing_decision,
            "applicant": payload,
            "readiness": {
                "score": readiness_res["score"],
                "band": final_verdict,
                "components": readiness_res["components"],
                "metadata": e5_metadata,
            },
            "archetype": {
                **livelihood_res,
                "is_unclassified": bool(livelihood_res.get("cluster_id", 0) == 0),
            },
            "explanation": recommendations_res
        }

    # 5. Strict Fail-Closed Audit Commit
    # Audit log record details
    audit_record = {
        "correlation_id": correlation_id,
        "timestamp": timestamp,
        "api_version": API_VERSION,
        "request_schema_version": REQUEST_SCHEMA_VERSION,
        "decision_version": DECISION_VERSION,
        "recommendation_version": RECOMMENDATION_VERSION,
        "model_lineage_bind": get_model_lineage_bind(),
        "final_verdict": final_verdict,
        "engine_statuses": engine_statuses,
        "triggered_rule_ids": triggered_rule_ids,
        "policy_override_flags": policy_override_flags,
        "request_payload_hash": request_payload_hash,
        "user_type_original": routing_decision.get("original_user_type"),
        "routing_decision": routing_decision,
        "serialized_response_json": json.dumps(response),
    }
    
    # Must succeed or it will raise AuditLogError (fail-closed)
    write_audit_record(audit_record)
    
    # Inject correlation_id to response header or body metadata
    response["correlation_id"] = correlation_id
    
    return response
