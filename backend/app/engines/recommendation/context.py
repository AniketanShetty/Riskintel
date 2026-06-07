import copy
from typing import Dict, Any

# Immutable attributes that must never reach the rule evaluator
PROTECTED_CLASSES = {
    "age", "gender", "marital_status", "social_class", 
    "education", "years_at_current_employer", "self_employed",
    "dependents", "young_dependents", "old_dependents", "occupants_count"
}

def build_person_a_context(inputs: Dict[str, Any], eligibility_res: Dict[str, Any], risk_tier_res: Dict[str, Any], archetype_res: Dict[str, Any]) -> Dict[str, Any]:
    ctx = {}
    # Safe copy of inputs, stripping protected classes
    ctx['inputs'] = {k: v for k, v in inputs.items() if k not in PROTECTED_CLASSES}
    # Attach engine results
    ctx['eligibility'] = copy.deepcopy(eligibility_res)
    ctx['risk_tier'] = copy.deepcopy(risk_tier_res)
    ctx['archetype'] = copy.deepcopy(archetype_res)
    return ctx

def build_person_b_context(inputs: Dict[str, Any], readiness_res: Dict[str, Any], livelihood_res: Dict[str, Any]) -> Dict[str, Any]:
    ctx = {}
    ctx['inputs'] = {k: v for k, v in inputs.items() if k not in PROTECTED_CLASSES}
    ctx['readiness'] = copy.deepcopy(readiness_res)
    ctx['livelihood'] = copy.deepcopy(livelihood_res)
    return ctx
