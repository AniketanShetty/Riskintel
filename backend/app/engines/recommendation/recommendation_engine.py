import logging
from app.engines.recommendation.context import build_person_a_context, build_person_b_context
from app.engines.recommendation.evaluator import evaluate_rules
from app.engines.recommendation.rules_person_a import PERSON_A_RULES
from app.engines.recommendation.rules_person_b import PERSON_B_RULES

logger = logging.getLogger(__name__)

RECOMMENDATION_VERSION = "1.2"

def generate_person_a_recommendations(inputs, eligibility_res, risk_tier_res, archetype_res):
    ctx = build_person_a_context(inputs, eligibility_res, risk_tier_res, archetype_res)
    factors, triggered_ids = evaluate_rules(PERSON_A_RULES, ctx, max_factors=5)
    logger.info(f"Person A Assessment triggered rules: {triggered_ids}")
    
    output = {
        'contributing_factors': factors,
        'recommendation_version': RECOMMENDATION_VERSION,
        'triggered_rule_ids': triggered_ids
    }
    return output

def generate_person_b_recommendations(inputs, readiness_res, livelihood_res):
    ctx = build_person_b_context(inputs, readiness_res, livelihood_res)
    factors, triggered_ids = evaluate_rules(PERSON_B_RULES, ctx, max_factors=5)
    logger.info(f"Person B Assessment triggered rules: {triggered_ids}")
    
    output = {
        'contributing_factors': factors,
        'recommendation_version': RECOMMENDATION_VERSION,
        'triggered_rule_ids': triggered_ids
    }
    return output

