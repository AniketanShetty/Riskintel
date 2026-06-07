from app.engines.recommendation.schema import Rule

def is_ready(ctx):
    return ctx.get('readiness', {}).get('band') == 'Ready'

def is_not_ready(ctx):
    return ctx.get('readiness', {}).get('band') == 'Not Ready'

def has_low_component(ctx, component_name):
    components = ctx.get('readiness', {}).get('components', {})
    if not components:
        return False
    sorted_comps = sorted(components.items(), key=lambda x: x[1].get('score', 100))
    lowest = [k for k, v in sorted_comps[:2]]
    return component_name in lowest

PERSON_B_RULES = [
    # Fallback Rules
    Rule("B-FALLBACK-001", "strengths", 0, lambda ctx: True, "No specific strengths identified based on current thresholds.", lambda ctx: {}),
    Rule("B-FALLBACK-002", "improvement_areas", 0, lambda ctx: True, "No specific improvement areas identified.", lambda ctx: {}),
    Rule("B-FALLBACK-003", "recommendations", 0, lambda ctx: True, "Continue monitoring business readiness indicators.", lambda ctx: {}),
    Rule("B-FALLBACK-004", "next_steps", 0, lambda ctx: True, "Maintain accurate business records.", lambda ctx: {}),
    
    # Strengths (Anchored)
    Rule(
        "B-STR-001", "strengths", 100,
        lambda ctx: not is_not_ready(ctx) and ctx.get('readiness', {}).get('band') == 'Ready',
        "Overall business readiness indicates strong debt capacity.",
        lambda ctx: {}
    ),
    Rule(
        "B-STR-002", "strengths", 90,
        lambda ctx: not is_not_ready(ctx) and not has_low_component(ctx, 'financial_health'),
        "Financial health and income coverage appear stable.",
        lambda ctx: {}
    ),
    # Anchor for Not Ready
    Rule(
        "B-STR-003", "strengths", 100,
        lambda ctx: is_not_ready(ctx) and not has_low_component(ctx, 'housing_stability'),
        "Housing stability is strong, though core financial metrics require attention.",
        lambda ctx: {}
    ),

    # Improvement Areas
    Rule(
        "B-IMP-001", "improvement_areas", 100,
        lambda ctx: has_low_component(ctx, 'financial_health'),
        "Financial health indicators show limited debt absorption capacity.",
        lambda ctx: {}
    ),
    Rule(
        "B-IMP-002", "improvement_areas", 90,
        lambda ctx: has_low_component(ctx, 'business_viability'),
        "Business viability metrics indicate operational fragility.",
        lambda ctx: {}
    ),

    # Recommendations (Educational/Passive)
    Rule(
        "B-REC-001", "recommendations", 100,
        lambda ctx: has_low_component(ctx, 'financial_health'),
        "Micro-enterprises with established daily savings habits generally build better readiness over time.",
        lambda ctx: {}
    ),
    Rule(
        "B-REC-002", "recommendations", 90,
        lambda ctx: has_low_component(ctx, 'business_viability'),
        "Formalizing business documentation typically strengthens viability assessments.",
        lambda ctx: {}
    ),

    # Next Steps
    Rule(
        "B-ACT-001", "next_steps", 100,
        lambda ctx: has_low_component(ctx, 'financial_health'),
        "Evaluate options for structured micro-savings products.",
        lambda ctx: {}
    ),
]
