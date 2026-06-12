from app.engines.recommendation.schema import ExplanationRule
from app.engines.recommendation.translations import humanize
from app.engines.readiness.readiness_engine import ReadinessEngine
from app.exceptions import GovernanceError

# Read engine-class SSOT constant for B-STR-002 absolute-threshold gate.
# ReadinessEngine.STRONG_STATUS_MIN is the engine's "Strong" cutoff (70).
# Reading via class attribute preserves the SSOT chain: the rule consumes
# the same number the engine consumes internally; if the engine ever
# changes the constant, the rule gate updates in lock-step.
_STRONG_STATUS_MIN = ReadinessEngine.STRONG_STATUS_MIN


def _required_threshold(ctx, dotted_path):
    """
    Read a threshold value from ctx using a dotted path. Raises
    GovernanceError if missing — fail-loud governance so a missing SSOT
    block is detected rather than silently substituted.
    """
    cur = ctx
    for part in dotted_path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            raise GovernanceError(
                f"Required governance threshold missing at '{dotted_path}'. "
                f"Refusing to substitute a hardcoded value.",
                governance_key=dotted_path,
            )
        cur = cur[part]
    if cur is None:
        raise GovernanceError(
            f"Required governance threshold at '{dotted_path}' is None.",
            governance_key=dotted_path,
        )
    return cur

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


def is_component_below_strong_threshold(ctx, component_name):
    """
    True when the named readiness component's score is strictly below the
    engine-defined "Strong" threshold (readiness.thresholds.strong_status_min,
    surfaced by E5 from ReadinessEngine.STRONG_STATUS_MIN).

    Replaces the bottom-2 ranking heuristic in the three rules that frame
    a Strong component as needing improvement. A component classified as
    "Strong" by E5 (score >= strong_status_min) must never trigger an
    improvement rule.

    Governance: follows the same fail-loud discipline as _required_threshold —
    raises GovernanceError if the named component or the strong_status_min
    threshold is missing from the response. No hardcoded threshold values.
    """
    comp = ctx.get('readiness', {}).get('components', {}).get(component_name)
    if comp is None:
        raise GovernanceError(
            f"Required readiness component '{component_name}' missing from response.",
            governance_key=f"readiness.components.{component_name}",
        )
    score = comp.get('score')
    if score is None:
        raise GovernanceError(
            f"Required readiness component '{component_name}' has no score.",
            governance_key=f"readiness.components.{component_name}.score",
        )
    # Read strong_status_min from the engine-provided SSOT block. If missing,
    # _required_threshold raises GovernanceError with the right governance_key.
    strong_min = _required_threshold(
        ctx, "readiness.thresholds.strong_status_min"
    )
    return score < strong_min

PERSON_B_RULES = [
    # Guardrail Policies
    ExplanationRule(
        rule_id="B-POLICY-001",
        feature_name="policy_override",
        priority=99,
        condition_callable=lambda ctx: "OVERRIDE_E5_FLOOR_BREACH" in ctx.get('readiness', {}).get('policy_override_flags', []),
        evidence_callable=lambda ctx: "Financial health score is critically low (floor breach).",
        reason_template="Your financial health metrics indicate insufficient current capacity to take on new debt.",
        advice_template="We cannot recommend a loan at this time. Focus on increasing your operational cash flow and documenting your revenue sources before reapplying.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["readiness.policy_override_flags"]
    ),
    ExplanationRule(
        rule_id="B-POLICY-002",
        feature_name="policy_override",
        priority=98,
        condition_callable=lambda ctx: "OVERRIDE_EXTREME_DEBT" in ctx.get('readiness', {}).get('policy_override_flags', []),
        evidence_callable=lambda ctx: "Requested loan amount exceeds mathematical serviceability compared to documented annual income.",
        reason_template="The requested loan amount is mathematically unserviceable given your current documented annual income.",
        advice_template="We cannot recommend a loan of this size. Consider requesting a significantly smaller loan amount that aligns with your current revenue.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["readiness.policy_override_flags"]
    ),
    ExplanationRule(
        rule_id="B-POLICY-003",
        feature_name="policy_override",
        priority=85,
        condition_callable=lambda ctx: "FLAG_PURPOSE_MISMATCH" in ctx.get('readiness', {}).get('policy_override_flags', []),
        evidence_callable=lambda ctx: "Loan purpose does not align with primary business.",
        reason_template="The requested loan purpose does not align with your primary documented business sector.",
        advice_template="Your application has been flagged for manual review. A loan officer will contact you to verify the business use-case for these funds.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["readiness.policy_override_flags"]
    ),
    ExplanationRule(
        rule_id="B-POLICY-004",
        feature_name="policy_override",
        priority=84,
        condition_callable=lambda ctx: "FLAG_LOW_INCOME_REVIEW" in ctx.get('readiness', {}).get('policy_override_flags', []),
        evidence_callable=lambda ctx: "Annual income is below standard threshold.",
        reason_template="Your documented annual income falls below standard microfinance thresholds.",
        advice_template="While your application is proceeding, a loan officer may request additional documentation to verify your ability to manage household expenses alongside loan payments.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["readiness.policy_override_flags"]
    ),

    # Fallback Rule
    # Freeze-blocker fix F1-B (parallel to F1 in rules_person_a.py): this
    # rule is gated to non-negative readiness bands so a "Not Ready" or
    # "Needs Improvement" applicant never sees "no specific area urgently
    # needs improvement" — that text contradicts a negative band.
    ExplanationRule(
        rule_id="B-FALLBACK-001",
        feature_name="overall_business_profile",
        priority=0,
        condition_callable=lambda ctx: ctx.get('readiness', {}).get('band') not in ('Not Ready', 'Needs Improvement'),
        evidence_callable=lambda ctx: "Your business profile falls within typical ranges.",
        reason_template="The system did not find any specific area that urgently needs improvement.",
        advice_template="Continue to focus on steadying your business income and managing your expenses.",
        format_args_callable=lambda ctx: {}
    ),

    # Strengths
    ExplanationRule(
        rule_id="B-STR-001",
        feature_name="overall_readiness",
        priority=100,
        condition_callable=lambda ctx: not is_not_ready(ctx) and is_ready(ctx),
        evidence_callable=lambda ctx: f"Overall readiness band: {ctx.get('readiness', {}).get('band', 'N/A')}.",
        reason_template="Your overall readiness shows strong ability to take on a loan and stable business operations.",
        advice_template="Keep up your current habits to stay eligible.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["readiness.band"]
    ),
    ExplanationRule(
        rule_id="B-STR-002",
        feature_name="financial_health",
        priority=90,
        # Freeze-blocker fix F2: absolute threshold (STRONG_STATUS_MIN)
        # rather than the bottom-2 component ranking. The rule now fires
        # only when the applicant genuinely has strong financial health
        # (score >= STRONG_STATUS_MIN), independent of how the other 4
        # components rank.
        condition_callable=lambda ctx: (
            not is_not_ready(ctx)
            and ctx.get('readiness', {}).get('components', {}).get('financial_health', {}).get('score', 0) >= _STRONG_STATUS_MIN
        ),
        # Freeze-blocker fix F4: evidence_callable now reads the applicant's
        # actual annual_income and monthly_expenses from inputs (not in the
        # protected-classes list, so the context builder passes them through).
        # The reason text was rewritten in the same change: it can now only
        # be true when fh >= STRONG_STATUS_MIN, by construction of the engine
        # formula (income_expense_ratio > 1 at that point).
        evidence_callable=lambda ctx: (
            f"Savings and income stability score: {ctx.get('readiness', {}).get('components', {}).get('financial_health', {}).get('score', 'N/A')}. "
            f"Annual income ₹{int(ctx.get('inputs', {}).get('annual_income', 0)):,}; "
            f"monthly expenses ₹{int(ctx.get('inputs', {}).get('monthly_expenses', 0)):,}."
        ),
        reason_template="Your savings and income stability score is {fh_score}, which indicates your income covers your expenses with room to spare.",
        advice_template="Continue to keep your business expenses well below your annual income.",
        format_args_callable=lambda ctx: {
            "fh_score": ctx.get('readiness', {}).get('components', {}).get('financial_health', {}).get('score', 'N/A'),
        },
        advice_type="generic",
        evidence_sources=[
            "readiness.components.financial_health.score",
            "inputs.annual_income",
            "inputs.monthly_expenses",
        ]
    ),
    ExplanationRule(
        rule_id="B-STR-003",
        feature_name="housing_stability",
        priority=80,
        condition_callable=lambda ctx: is_not_ready(ctx) and not is_component_below_strong_threshold(ctx, 'housing_stability'),
        evidence_callable=lambda ctx: f"Housing situation score: {ctx.get('readiness', {}).get('components', {}).get('housing_stability', {}).get('score', 'N/A')}.",
        reason_template="Your stable housing situation provides a strong foundation for your application.",
        advice_template="Your home stability is a major strength; focus your next steps on the specific improvement areas listed below.",
        format_args_callable=lambda ctx: {},
        advice_type="inferred",
        evidence_sources=["readiness.band", "readiness.components.housing_stability.score"]
    ),

    # Improvement Areas
    ExplanationRule(
        rule_id="B-IMP-001",
        feature_name="financial_health",
        priority=100,
        condition_callable=lambda ctx: is_component_below_strong_threshold(ctx, 'financial_health'),
        evidence_callable=lambda ctx: f"Savings and income stability score: {ctx.get('readiness', {}).get('components', {}).get('financial_health', {}).get('score', 'N/A')}.",
        reason_template="Your savings and income stability score is {fh_score}. Profiles with a score above {strong_min} generally show a stronger ability to repay comfortably.",
        advice_template="Building a savings buffer and steadying your monthly cash flow can raise this score over time, though reaching {strong_min} does not guarantee a Ready outcome.",
        format_args_callable=lambda ctx: {
            "fh_score": ctx.get('readiness', {}).get('components', {}).get('financial_health', {}).get('score', 'N/A'),
            # Fail-loud governance: require the engine-provided SSOT block.
            # Missing strong_status_min indicates a contract violation;
            # raise instead of silently substituting a hardcoded value.
            "strong_min": _required_threshold(
                ctx, "readiness.thresholds.strong_status_min",
            ),
        },
        advice_type="evidence_based",
        evidence_sources=[
            "readiness.components.financial_health.score",
            "readiness.metadata.e5_thresholds.strong_status_min",
        ]
    ),
    ExplanationRule(
        rule_id="B-IMP-002",
        feature_name="business_viability",
        priority=90,
        # Freeze-blocker fix F3: rule fires only when business_viability is
        # one of the bottom 2 components AND the loan purpose is genuinely
        # misaligned with the applicant's main business activity. The
        # 'Neutral' alignment case is left in scope (a partial mismatch is
        # still worth advising on); only 'Aligned' is suppressed.
        condition_callable=lambda ctx: (
            is_component_below_strong_threshold(ctx, 'business_viability')
            and ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('factors', {}).get('purpose_alignment') == 'Misaligned'
        ),
        evidence_callable=lambda ctx: (
            f"Business stability score: {ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('score', 'N/A')}. "
            f"Loan purpose alignment: {ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('factors', {}).get('purpose_alignment', 'Unknown')}. "
            f"Has secondary income: {ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('factors', {}).get('has_secondary_income', False)}."
        ),
        reason_template=(
            "Your business stability score is {bv_score}. The engine found a {alignment_label} match between the loan purpose you selected and your main business activity ({primary_business_raw})."
        ),
        # Final-Explainability Patch 2: coaching-safe wording. The previous
        # advice ("Choosing a loan purpose that more closely matches …")
        # could be read as "change the dropdown answer". This rewrite
        # frames the issue as a business-reality one and explicitly
        # rejects the idea that re-applying under a different purpose
        # is the path forward.
        advice_template=(
            "Approval here depends on the loan genuinely supporting your primary business, not on paperwork or on choosing a different purpose on the form. Where the loan would actually fund something you do, that strengthens the application. Where it would not, the application is unlikely to be approved regardless of the stated purpose. If you are not sure how the loan would be used, speak with a loan advisor before re-applying."
        ),
        format_args_callable=lambda ctx: {
            "bv_score": ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('score', 'N/A'),
            "alignment_label": (ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('factors', {}).get('purpose_alignment') or 'Unknown').lower(),
            "primary_business_raw": ctx.get('readiness', {}).get('components', {}).get('business_viability', {}).get('factors', {}).get('primary_business', 'your main business'),
        },
        advice_type="evidence_based",
        evidence_sources=[
            "readiness.components.business_viability.score",
            "readiness.components.business_viability.factors.purpose_alignment",
            "readiness.components.business_viability.factors.primary_business"
        ]
    ),
]
