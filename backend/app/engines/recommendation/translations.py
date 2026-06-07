"""
Human-language translation layer for applicant-facing explanation prose.

Maps internal feature keys (snake_case, often raw DB column names) and
policy jargon (premium-tier, eligibility profile, etc.) into plain language
that a first-time loan applicant can understand.

Scope:
    Applied to *rendered text only* — reason, evidence, improvement_advice.
    Does NOT modify the `feature_name` field on ExplanationFactor, which is
    part of the frozen API contract.

Usage:
    from app.engines.recommendation.translations import humanize, FEATURE_TRANSLATIONS
    humanize("loan_amount")              -> "requested loan amount"
    humanize("financial_health")         -> "savings and income stability"
    humanize("P1")                       -> "premium"
    humanize("premium-tier")             -> "premium"
    humanize("eligibility profile")      -> "overall eligibility"
    humanize("annual_income", money=True)
        -> "yearly income of ₹3,00,000"   (when the value is numeric)
"""
from typing import Any

# ── Feature key → plain language map ────────────────────────────────────────

FEATURE_TRANSLATIONS: dict = {
    # Person A raw input keys
    "loan_amount": "requested loan amount",
    "annual_income": "yearly income",
    "residential_assets_value": "value of property you own",
    "commercial_assets_value": "value of business property",
    "luxury_assets_value": "value of high-value possessions",
    "bank_asset_value": "value of savings and deposits",
    "cibil_score": "credit score",
    "loan_term": "loan tenure",
    "loan_purpose": "loan purpose",
    "dependents": "dependents",
    "self_employed": "self-employment status",
    "years_at_current_employer": "years at current job",
    "education": "education",
    "marital_status": "marital status",

    # Person B raw input keys
    "primary_business": "main business activity",
    "secondary_business": "side business",
    "monthly_expenses": "monthly expenses",
    "loan_tenure": "loan tenure",
    "loan_installments": "number of instalments",
    "young_dependents": "young dependents",
    "old_dependents": "older dependents",
    "occupants_count": "household size",
    "home_ownership": "home ownership",
    "type_of_house": "type of house",
    "house_area": "house size",
    "sanitary_availability": "sanitary access",
    "water_availability": "water access",
    "social_class": "social category",

    # Person B component names
    "financial_health": "savings and income stability",
    "housing_stability": "housing situation",
    "infrastructure_access": "basic amenities access",
    "household_burden": "household responsibilities",
    "business_viability": "business stability and records",
    "overall_readiness": "overall readiness",
    "overall_business_profile": "overall business profile",
    "overall_profile": "overall profile",
}

# ── Tier / jargon → plain language ─────────────────────────────────────────

TIER_TRANSLATIONS: dict = {
    "P1": "premium",
    "P2": "mid",
    "P3": "elevated",
    "P4": "high",
    "premium-tier": "premium",
    "mid-tier": "mid",
    "elevated-tier": "elevated",
    "high-tier": "high",
    "eligibility profile": "overall eligibility",
    "readiness profile": "overall readiness",
    "repayment readiness": "ability to repay comfortably",
    "default probability": "likelihood of missed repayments",
    "collateral backing": "assets to support the loan",
    "principal": "loan size",
    "credit utilization": "use of available credit",
    "hard inquiries": "recent credit checks",
    "micro-savings": "small regular savings",
    "debt absorption capacity": "ability to take on more debt",
    "debt-to-income burden": "loan size relative to income",
}


def _format_money(value: Any) -> str:
    """Format a numeric value as a friendly Indian-locale money string."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(n) >= 1_00_00_000:  # 1 crore
        return f"₹{n/1_00_00_000:.2f} crore"
    if abs(n) >= 1_00_000:  # 1 lakh
        return f"₹{n/1_00_000:.2f} lakh"
    if abs(n) >= 1_000:
        return f"₹{n:,.0f}"
    return f"₹{n:.0f}"


def humanize(raw: Any, money: bool = False) -> str:
    """
    Convert a raw feature key, tier label, or jargon phrase into plain language.

    Args:
        raw: The raw string (or any value) to translate. Non-strings are
            returned unchanged.
        money: If True and the value is numeric, format as a money string
            (₹1,50,000 / ₹2.50 lakh / ₹1.20 crore).

    Returns:
        Plain-language string. Unknown values are returned as-is so we never
        silently drop information.
    """
    if not isinstance(raw, str):
        return raw

    # Direct match in feature map
    if raw in FEATURE_TRANSLATIONS:
        return FEATURE_TRANSLATIONS[raw]

    # Tier / jargon map (whole-string match)
    if raw in TIER_TRANSLATIONS:
        return TIER_TRANSLATIONS[raw]

    # Substring replacement for compound phrases containing jargon
    translated = raw
    for jargon, plain in TIER_TRANSLATIONS.items():
        if jargon in translated:
            translated = translated.replace(jargon, plain)

    if money:
        return _format_money(translated)
    return translated
