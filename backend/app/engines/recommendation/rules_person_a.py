from app.engines.recommendation.schema import ExplanationRule
from app.engines.recommendation.translations import humanize, _format_money
from app.exceptions import GovernanceError

# ── Actionability whitelist ────────────────────────────────────────────────
# Only features in this set may drive automated applicant-facing improvement
# advice. Features outside the set (e.g. annual_income, dependents, education)
# can still appear in `feature_contributions` and downstream scoring, but
# they MUST NOT generate action language — they are non-actionable from the
# applicant's perspective in the short term. See 2026-06-07 feature audit.
ACTIONABLE_FEATURES = frozenset({
    "loan_amount",
    "loan_term",
    "cibil_score",
})

# Generic fallback text for A-STR-003 when no actionable blocking factor
# can be identified. Used as a safety net so the engine never invents advice
# for non-actionable profile attributes.
A_STR_003_FALLBACK = {
    "evidence": "Your credit score is strong, but the engine could not isolate a single application detail that you can change right now.",
    "reason": "Your credit history looks good, but we cannot point to one application detail that you can quickly change.",
    "advice": "We cannot identify a single application detail that you can immediately change. Speak with a loan advisor about your overall application profile before applying again.",
}


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

def _actionable_top_negative(ctx):
    """
    Return the humanized name of the strongest negative contributor whose
    feature key is in ACTIONABLE_FEATURES, or None if no such contributor
    exists (e.g. only non-actionable features like annual_income or
    dependents are weighing negatively).
    """
    contribs = ctx.get('eligibility', {}).get('feature_contributions', {})
    if not contribs:
        return None
    # Sort ascending by contribution value (most negative first)
    for feature, value in sorted(contribs.items(), key=lambda x: x[1]):
        if value < 0 and feature in ACTIONABLE_FEATURES:
            return humanize(feature)
    return None


def _required_threshold(ctx, dotted_path):
    """
    Read a threshold value from ctx using a dotted path. Raises
    GovernanceError if the value is missing — fail-loud governance so
    a missing SSOT block is detected rather than silently substituted
    with a hardcoded fallback.
    """
    cur = ctx
    for part in dotted_path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            raise GovernanceError(
                f"Required governance threshold missing at '{dotted_path}'. "
                f"This indicates a contract violation in the engine/SSOT "
                f"chain. Refusing to substitute a hardcoded value.",
                governance_key=dotted_path,
            )
        cur = cur[part]
    if cur is None:
        raise GovernanceError(
            f"Required governance threshold at '{dotted_path}' is None.",
            governance_key=dotted_path,
        )
    return cur

PERSON_A_RULES = [
    # Fallback Rule
    # Freeze-blocker fix F1: this rule is gated to non-negative verdicts so
    # a rejected applicant never sees "no major weakness" or "no urgent
    # improvement area" — that text contradicts a negative verdict.
    ExplanationRule(
        rule_id="A-FALLBACK-001",
        feature_name="overall_profile",
        priority=0,
        condition_callable=lambda ctx: ctx.get('eligibility', {}).get('verdict') in ('Highly Likely', 'Likely'),
        evidence_callable=lambda ctx: "Your overall application does not show any major single weakness.",
        reason_template="The system did not find any specific area that urgently needs improvement.",
        advice_template="Reviewing your application details regularly is the best way to maintain a strong profile.",
        format_args_callable=lambda ctx: {}
    ),

    # Standard Strengths
    ExplanationRule(
        rule_id="A-STR-001",
        feature_name="cibil_score",
        priority=100,
        condition_callable=lambda ctx: is_verdict_favorable(ctx) and ctx.get('risk_tier', {}).get('tier') == 'P1',
        evidence_callable=lambda ctx: f"Your credit score is {ctx.get('inputs', {}).get('cibil_score', 'N/A')}.",
        reason_template="Your credit score shows a strong history of repaying on time, placing you in our premium band.",
        advice_template="Keep your credit use steady and continue paying on time to stay in the premium band.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["inputs.cibil_score", "risk_tier.tier"]
    ),
    ExplanationRule(
        rule_id="A-STR-002",
        feature_name="residential_assets_value",
        priority=90,
        condition_callable=lambda ctx: is_verdict_favorable(ctx) and is_top_positive_contributor(ctx, 'residential_assets_value'),
        evidence_callable=lambda ctx: f"Value of property you own on record: {_format_money(ctx.get('inputs', {}).get('residential_assets_value', 'N/A'))}.",
        reason_template="The property you own adds strong support to your application.",
        advice_template="Your property value is a strong anchor for your application; continue to maintain this asset.",
        format_args_callable=lambda ctx: {},
        advice_type="generic",
        evidence_sources=["inputs.residential_assets_value", "eligibility.feature_contributions.residential_assets_value"]
    ),

    # Strengths for Unlikely (Anchored Contextualization) — ACTIONABLE PATH
    # Fires when an actionable negative contributor (loan_amount, loan_term,
    # cibil_score) is the strongest negative force in feature_contributions.
    ExplanationRule(
        rule_id="A-STR-003",
        feature_name="cibil_score",
        priority=80,
        condition_callable=lambda ctx: (
            not is_verdict_favorable(ctx)
            and ctx.get('risk_tier', {}).get('tier') in ['P1', 'P2']
            and _actionable_top_negative(ctx) is not None
        ),
        evidence_callable=lambda ctx: f"Your credit score is {ctx.get('inputs', {}).get('cibil_score', 'N/A')}; the area weighing most against you right now is: {_actionable_top_negative(ctx)}.",
        reason_template="Your credit score of {cibil_score} is strong, but {blocking_factor} is currently weighing more heavily on the assessment than your credit history.",
        advice_template="Addressing {blocking_factor} while keeping your credit history stable is more likely to improve your overall eligibility than further credit-score work alone.",
        format_args_callable=lambda ctx: {
            "cibil_score": ctx.get('inputs', {}).get('cibil_score', 'N/A'),
            "blocking_factor": _actionable_top_negative(ctx),
        },
        advice_type="evidence_based",
        evidence_sources=["eligibility.feature_contributions"]
    ),

    # Strengths for Unlikely (Anchored Contextualization) — FALLBACK PATH
    # Fires when the strong-CIBIL case applies but no actionable negative
    # contributor exists (e.g. only non-actionable features like annual_income
    # or dependents weigh negatively). Emits generic safety-net copy.
    ExplanationRule(
        rule_id="A-STR-003-FALLBACK",
        feature_name="cibil_score",
        priority=80,
        condition_callable=lambda ctx: (
            not is_verdict_favorable(ctx)
            and ctx.get('risk_tier', {}).get('tier') in ['P1', 'P2']
            and _actionable_top_negative(ctx) is None
        ),
        evidence_callable=lambda ctx: A_STR_003_FALLBACK["evidence"],
        reason_template=A_STR_003_FALLBACK["reason"],
        advice_template=A_STR_003_FALLBACK["advice"],
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["eligibility.feature_contributions"]
    ),

    # Final-Explainability Patch 1: P4 override explainability.
    # Fires when the E2→E1 P4 override mutated the verdict to "Unlikely".
    # The signal is the (P4, Unlikely) co-occurrence — E1 alone would not
    # produce Unlikely for a CIBIL > 700 applicant, and tier P4 only
    # combines with the override when E1 had given a positive verdict.
    # Text explicitly names the policy so a mentor can explain the
    # rejection. priority=95 places it near the top of the factor list,
    # below the CIBIL premium rule (A-STR-001) so the borrower still
    # sees the CIBIL signal as primary when tier is P1.
    ExplanationRule(
        rule_id="A-POLICY-001",
        feature_name="policy_override",
        priority=95,
        condition_callable=lambda ctx: (
            ctx.get('eligibility', {}).get('verdict') == 'Unlikely'
            and ctx.get('risk_tier', {}).get('tier') == 'P4'
        ),
        evidence_callable=lambda ctx: (
            f"Your credit score of {ctx.get('inputs', {}).get('cibil_score', 'N/A')} places you in our highest-risk credit tier (P4), "
            f"which our policy requires to be declined even when other parts of the application are strong."
        ),
        reason_template=(
            "Your application has strengths, but our policy requires a stronger credit tier than what your current credit profile demonstrates."
        ),
        advice_template=(
            "Your current credit tier is the reason this application cannot be approved. Improving your credit profile is the single most impactful action. Reaching the P3 tier (credit score above 658) is a meaningful milestone — once your credit score is consistently above 658, please reapply. Approval is never guaranteed by reaching any score; the policy threshold exists to protect both you and the lender."
        ),
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=[
            "inputs.cibil_score",
            "risk_tier.tier",
            "audit.policy_override_flags",
        ]
    ),

    # Risk Factors
    ExplanationRule(
        rule_id="A-RISK-001",
        feature_name="loan_amount",
        priority=100,
        condition_callable=lambda ctx: (
            is_top_negative_contributor(ctx, 'loan_amount') and
            (ctx.get('inputs', {}).get('loan_amount', 0) / max(ctx.get('inputs', {}).get('annual_income', 1), 1)) > 0.3
        ),
        evidence_callable=lambda ctx: f"Requested loan amount: {_format_money(ctx.get('inputs', {}).get('loan_amount', 'N/A'))}.",
        reason_template="Your requested loan amount of {loan_amount} appears high relative to your yearly income of {annual_income}.",
        advice_template="Reducing the loan size to one that lines up more closely with your income can strengthen your profile, though no specific amount is guaranteed.",
        format_args_callable=lambda ctx: {
            "loan_amount": _format_money(ctx.get('inputs', {}).get('loan_amount', 'N/A')),
            "annual_income": _format_money(ctx.get('inputs', {}).get('annual_income', 'N/A')),
        },
        advice_type="evidence_based",
        evidence_sources=["inputs.loan_amount", "eligibility.feature_contributions.loan_amount"]
    ),
    ExplanationRule(
        rule_id="A-RISK-002",
        feature_name="cibil_score",
        priority=90,
        condition_callable=lambda ctx: is_top_negative_contributor(ctx, 'cibil_score'),
        evidence_callable=lambda ctx: f"Your credit score: {ctx.get('inputs', {}).get('cibil_score', 'N/A')}.",
        reason_template="Your current credit score is {cibil_score}. Premium-band applicants typically have a score above {p1_min}.",
        advice_template="Improving your credit profile over time can lower the perceived risk, though reaching {p1_min} does not guarantee approval.",
        format_args_callable=lambda ctx: {
            "cibil_score": ctx.get('inputs', {}).get('cibil_score', 'N/A'),
            # Fail-loud governance: require the engine-provided SSOT block.
            # Missing p1_min indicates a governance contract violation;
            # raise instead of silently substituting a hardcoded value.
            "p1_min": _required_threshold(
                ctx, "risk_tier.threshold_values.p1_min",
            ),
        },
        advice_type="evidence_based",
        evidence_sources=[
            "inputs.cibil_score",
            "eligibility.feature_contributions.cibil_score",
            "risk_tier.threshold_values.p1_min",
        ]
    ),

    # Age-Term Guardrail Override
    ExplanationRule(
        rule_id="A-POLICY-002",
        feature_name="policy_override",
        priority=98,
        condition_callable=lambda ctx: (
            "OVERRIDE_AGE_TERM_REJECTION" in ctx.get('eligibility', {}).get('policy_override_flags', [])
            and not is_verdict_favorable(ctx)
        ),
        evidence_callable=lambda ctx: (
            f"Your projected age at the end of the loan term ({ctx.get('eligibility', {}).get('maturity_age', 'N/A')} years) "
            f"exceeds our maximum allowable maturity age."
        ),
        reason_template="Our policy requires that all loans are fully repaid within the borrower's primary income-generating years (before age 70).",
        advice_template="Because your requested loan term pushes the maturity date past our age limit, this application cannot be approved. Consider reapplying with a shorter loan term or a younger co-applicant.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["eligibility.maturity_age", "audit.policy_override_flags"]
    ),

    # LTI Guardrail Override
    ExplanationRule(
        rule_id="A-POLICY-003",
        feature_name="policy_override",
        priority=97,
        condition_callable=lambda ctx: (
            "OVERRIDE_LTI_REJECTION" in ctx.get('eligibility', {}).get('policy_override_flags', [])
            and not is_verdict_favorable(ctx)
        ),
        evidence_callable=lambda ctx: (
            f"The requested loan amount is {round(ctx.get('eligibility', {}).get('lti', 0), 1)}x your annual income, "
            f"which exceeds our maximum allowable leverage ratio."
        ),
        reason_template="Our policy restricts loan amounts to a manageable multiple of your annual income to ensure monthly payments remain affordable.",
        advice_template="The requested loan amount is too high for your current income level. You must significantly reduce the loan amount to qualify under our affordability policy.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["eligibility.lti", "audit.policy_override_flags"]
    ),

    # Low Income Review Flag
    ExplanationRule(
        rule_id="A-POLICY-004",
        feature_name="policy_override",
        priority=85,
        condition_callable=lambda ctx: (
            "FLAG_LOW_INCOME_REVIEW" in ctx.get('eligibility', {}).get('policy_override_flags', [])
            and is_verdict_favorable(ctx)
        ),
        evidence_callable=lambda ctx: "Your reported annual income is below the standard urban subsistence threshold.",
        reason_template="While your credit profile is strong enough for approval, our policy requires manual review for incomes below this threshold to ensure the loan supports your long-term financial health.",
        advice_template="Your application is marked as 'Likely', but will undergo a mandatory manual review by a loan officer. Please be prepared to discuss the specific purpose of the loan.",
        format_args_callable=lambda ctx: {},
        advice_type="evidence_based",
        evidence_sources=["audit.policy_override_flags"]
    ),
]
