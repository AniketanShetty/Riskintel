from app.engines.recommendation.schema import Rule

def get_sorted_contributions(ctx):
    contributions = ctx.get('eligibility', {}).get('feature_contributions', {})
    return sorted(contributions.items(), key=lambda x: x[1])

def is_top_negative_contributor(ctx, feature, top_k=2):
    sorted_contribs = get_sorted_contributions(ctx)
    top_negative_features = [k for k, v in sorted_contribs[:top_k] if v < 0]
    return feature in top_negative_features

def is_top_positive_contributor(ctx, feature, top_k=2):
    sorted_contribs = get_sorted_contributions(ctx)
    top_positive_features = [k for k, v in sorted_contribs[-top_k:] if v > 0]
    return feature in top_positive_features

def is_verdict_favorable(ctx):
    return ctx.get('eligibility', {}).get('verdict') in ['Likely', 'Highly Likely']

PERSON_A_RULES = [
    # Fallback Rules
    Rule("A-FALLBACK-001", "strengths", 0, lambda ctx: True, "No specific strengths identified based on current thresholds.", lambda ctx: {}),
    Rule("A-FALLBACK-002", "risk_factors", 0, lambda ctx: True, "No specific risk factors identified.", lambda ctx: {}),
    Rule("A-FALLBACK-003", "recommendations", 0, lambda ctx: True, "Continue monitoring credit indicators.", lambda ctx: {}),
    Rule("A-FALLBACK-004", "action_plan", 0, lambda ctx: True, "Maintain current financial behaviors.", lambda ctx: {}),
    
    # Standard Strengths (Anchored)
    Rule(
        "A-STR-001", "strengths", 100,
        lambda ctx: is_verdict_favorable(ctx) and ctx.get('risk_tier', {}).get('tier') == 'P1',
        "Credit score ({score}) indicates strong repayment reliability.",
        lambda ctx: {'score': ctx.get('inputs', {}).get('cibil_score', 'N/A')}
    ),
    Rule(
        "A-STR-002", "strengths", 90,
        lambda ctx: is_verdict_favorable(ctx) and is_top_positive_contributor(ctx, 'residential_assets_value'),
        "High total asset value provides collateral backing.",
        lambda ctx: {}
    ),
    
    # Strengths for Unlikely (Anchored Contextualization)
    Rule(
        "A-STR-003", "strengths", 100,
        lambda ctx: not is_verdict_favorable(ctx) and ctx.get('risk_tier', {}).get('tier') in ['P1', 'P2'],
        "Historical credit score is strong, though current loan parameters reduce eligibility.",
        lambda ctx: {}
    ),

    # Risk Factors
    Rule(
        "A-RISK-001", "risk_factors", 100,
        lambda ctx: is_top_negative_contributor(ctx, 'loan_amount'),
        "Requested loan amount poses a high debt-to-income burden.",
        lambda ctx: {}
    ),
    Rule(
        "A-RISK-002", "risk_factors", 90,
        lambda ctx: is_top_negative_contributor(ctx, 'cibil_score'),
        "Current credit score falls below optimal premium tier thresholds.",
        lambda ctx: {}
    ),
    
    # Recommendations (Passive/Educational)
    Rule(
        "A-REC-001", "recommendations", 100,
        lambda ctx: is_top_negative_contributor(ctx, 'loan_amount'),
        "Borrowers with lower loan-to-income ratios generally demonstrate stronger repayment capacity.",
        lambda ctx: {}
    ),
    Rule(
        "A-REC-002", "recommendations", 90,
        lambda ctx: is_top_negative_contributor(ctx, 'cibil_score'),
        "A track record of timely payments over 6-12 months typically improves tier placement.",
        lambda ctx: {}
    ),

    # Action Plan
    Rule(
        "A-ACT-001", "action_plan", 100,
        lambda ctx: is_top_negative_contributor(ctx, 'loan_amount'),
        "Review if a lower principal amount meets core requirements.",
        lambda ctx: {}
    ),
    Rule(
        "A-ACT-002", "action_plan", 90,
        lambda ctx: is_top_negative_contributor(ctx, 'cibil_score'),
        "Monitor credit profile and minimize new hard inquiries.",
        lambda ctx: {}
    ),
]
