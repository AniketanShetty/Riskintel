from typing import List, Dict, Any, Tuple
import logging

from app.engines.recommendation.schema import ExplanationRule

logger = logging.getLogger(__name__)

def evaluate_rules(rules: List[ExplanationRule], context: Dict[str, Any], max_factors: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
    triggered_rules = []
    
    # First pass: evaluate standard rules (priority > 0)
    standard_rules = [r for r in rules if r.priority > 0]
    
    for rule in standard_rules:
        try:
            if rule.condition_callable(context):
                fmt_args = rule.format_args_callable(context)
                reason = rule.reason_template.format(**fmt_args)
                advice = rule.advice_template.format(**fmt_args)
                evidence = rule.evidence_callable(context)
                
                # Fetch value from inputs
                value = context.get('inputs', {}).get(rule.feature_name, "Unknown")
                
                factor_dict = {
                    "feature": rule.feature_name,
                    "value": value,
                    "evidence": evidence,
                    "reason": reason,
                    "improvement_advice": advice
                }
                
                triggered_rules.append((rule.priority, rule.rule_id, factor_dict))
        except Exception as e:
            logger.warning(f"Error evaluating rule {rule.rule_id}: {e}")
            
    # Sort and truncate
    final_factors = []
    final_triggered_ids = []
    
    # Sort by priority DESC, then rule_id ASC
    sorted_items = sorted(triggered_rules, key=lambda x: (-x[0], x[1]))
    
    # Truncate
    truncated = sorted_items[:max_factors]
    
    if truncated:
        for item in truncated:
            final_triggered_ids.append(item[1])
            final_factors.append(item[2])
    else:
        # Fallback evaluation (priority == 0)
        fallback_rules = [r for r in rules if r.priority == 0]
        fallback_rules = sorted(fallback_rules, key=lambda x: x.rule_id)
        for rule in fallback_rules:
            try:
                if rule.condition_callable(context):
                    final_triggered_ids.append(rule.rule_id)
                    fmt_args = rule.format_args_callable(context)
                    reason = rule.reason_template.format(**fmt_args)
                    advice = rule.advice_template.format(**fmt_args)
                    evidence = rule.evidence_callable(context)
                    
                    value = context.get('inputs', {}).get(rule.feature_name, "Unknown")
                    
                    factor_dict = {
                        "feature": rule.feature_name,
                        "value": value,
                        "evidence": evidence,
                        "reason": reason,
                        "improvement_advice": advice
                    }
                    final_factors.append(factor_dict)
                    break # Only one fallback needed
            except Exception as e:
                logger.warning(f"Error evaluating fallback rule {rule.rule_id}: {e}")
                
    return final_factors, final_triggered_ids
