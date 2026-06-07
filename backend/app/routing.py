"""
routing.py

Handles pipeline routing based on CIBIL scores and user profiles.
"""
from typing import Dict, Any, Tuple

def convert_person_a_to_person_b(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a Person A context/payload to Person B context.
    Ensures all required fields for E5 (Readiness Engine) and E6 (Livelihood Mapper)
    are present with valid types and default values.
    """
    dependents = int(payload.get("dependents", 0))
    loan_term_years = int(payload.get("loan_term", 1))
    
    # Calculate housing values from assets
    res_assets = float(payload.get("residential_assets_value", 0))
    home_ownership = 1 if res_assets > 0 else 0
    type_of_house = "T1" if res_assets > 1000000 else ("T2" if res_assets > 0 else "R")
    
    # Estimate monthly expenses if not provided (default to a safe 30% of monthly income)
    annual_income = int(payload.get("annual_income", 0))
    monthly_income = annual_income // 12
    monthly_expenses = int(payload.get("monthly_expenses") or max(1000, int(monthly_income * 0.3)))
    
    converted = {
        "full_name": payload.get("full_name", "Anonymous"),
        "age": int(payload.get("age", 30)),
        "gender": payload.get("gender", "M"),
        # Map primary business from loan_purpose or fallback
        "primary_business": payload.get("primary_business") or payload.get("loan_purpose") or "Services",
        "secondary_business": payload.get("secondary_business", "none"),
        "annual_income": annual_income,
        "monthly_expenses": monthly_expenses,
        "loan_amount": int(payload.get("loan_amount", 0)),
        "loan_purpose": payload.get("loan_purpose", "personal"),
        # Loan tenure is in months for Person B
        "loan_tenure": int(payload.get("loan_tenure") or (loan_term_years * 12)),
        "loan_installments": int(payload.get("loan_installments") or (loan_term_years * 12)),
        "young_dependents": dependents,
        "old_dependents": 0,
        "occupants_count": dependents + 1,
        "home_ownership": home_ownership,
        "type_of_house": type_of_house,
        "house_area": int(payload.get("house_area", 450)),
        "sanitary_availability": int(payload.get("sanitary_availability", 1)),
        "water_availability": float(payload.get("water_availability", 1.0)),
        "social_class": payload.get("social_class", "GEN")
    }
    return converted

def route_pipeline(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], list, Dict[str, str]]:
    """
    Evaluates the input payload and routes to either Person A or Person B pipeline.

    Returns:
        Tuple[str, Dict[str, Any], list, Dict[str, str]]:
            - Routed pipeline type ("person_a" or "person_b")
            - Formatted payload for the routed pipeline
            - List of routing flags injected (e.g. "REROUTE_NTC_TO_PERSON_B")
            - Structured routing decision:
                { "original_user_type": str, "routed_to": str, "reason": str }
    """
    user_type = payload.get("user_type", "person_a")
    cibil_score = payload.get("cibil_score")

    routing_flags: list = []
    original_user_type = user_type

    # Try parsing cibil score if present
    cibil_val = None
    if cibil_score is not None:
        try:
            cibil_val = int(cibil_score)
        except (ValueError, TypeError):
            pass

    def _decision(routed: str, reason: str) -> Dict[str, str]:
        return {
            "original_user_type": original_user_type,
            "routed_to": routed,
            "reason": reason,
        }

    # Explicit override: CIBIL == 0 or -1 reroutes to Person B Flow
    if user_type == "person_a" and cibil_val in (0, -1):
        routing_flags.append("REROUTE_NTC_TO_PERSON_B")
        converted_payload = convert_person_a_to_person_b(payload)
        return "person_b", converted_payload, routing_flags, _decision("person_b", "cibil_absent_or_sentinel")

    if user_type == "person_b" or cibil_val is None:
        reason = "user_type_person_b_or_cibil_absent"
        return "person_b", payload, routing_flags, _decision("person_b", reason)

    return "person_a", payload, routing_flags, _decision("person_a", "standard_person_a_pipeline")
