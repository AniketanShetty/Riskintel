from models.session import ApplicationSession
from schemas.api_models import (
    DecisionExplanation,
    ApprovedTerms,
    CounterOffer,
    RejectionDetails,
    RepromptRequirements
)

def generate_decision_explanation(session: ApplicationSession) -> DecisionExplanation | None:
    """
    Generates a plain-language, non-judgmental explanation for the borrower
    based on the current FSM state and underlying models.
    """
    state = session.current_state

    if state == "READY":
        if not session.optimization_results:
            return None
        last_opt = session.optimization_results[-1]
        return DecisionExplanation(
            approved_terms=ApprovedTerms(
                final_loan_amount=last_opt.approved_loan_amount or session.loan_amount,
                final_tenure_months=last_opt.approved_tenure or session.loan_term,
                monthly_emi=last_opt.contract_emi,
                next_steps="Your loan is approved! The funds will be transferred to your account shortly."
            )
        )

    elif state == "NEARLY_READY":
        if not session.optimization_results:
            return None
        last_opt = session.optimization_results[-1]
        return DecisionExplanation(
            counter_offer=CounterOffer(
                reason="To keep your monthly payments safe and affordable, we extended the repayment time.",
                proposed_loan_amount=last_opt.approved_loan_amount or session.loan_amount,
                proposed_tenure_months=last_opt.approved_tenure or session.loan_term,
                proposed_monthly_emi=last_opt.contract_emi
            )
        )

    elif state == "NOT_READY_YET":
        if not session.state_events:
            return None
        # Find the event that caused NOT_READY_YET
        # It's typically the last event in the list
        last_event = session.state_events[-1]
        trigger = last_event.trigger_event

        reason = "We cannot proceed with your loan application at this time."
        advice = "Please try applying again in the future."

        if trigger == "MATH_WALL_HIT":
            reason = "The requested loan amount is too high for your currently verified income."
            advice = "Please try applying for a smaller amount, or apply with a co-applicant to combine your incomes."
        elif trigger in ("FO_UNREACHABLE_MAX_RETRIES", "FO_UNREACHABLE_TTL_EXPIRED"):
            reason = "We were unable to reach you to verify your details."
            advice = "Please ensure your phone is active and try applying again in 14 days."
        elif trigger == "BUREAU_TRUST_FAIL":
            reason = "We need a bit more credit history to approve this loan."
            advice = "Building a small, consistent repayment history first will help you qualify next time."
        elif trigger == "FO_FRAUD_DETECTED":
            reason = "We encountered an issue verifying your application details."
            advice = "Please ensure all information provided is accurate and apply again."
        elif trigger == "USER_REFUSAL":
            reason = "You have opted not to proceed with the verification."
            advice = "If you change your mind, you can start a new application at any time."
        elif trigger == "USER_REJECTS_COUNTER_OFFER":
            reason = "You declined the proposed counter-offer."
            advice = "You can apply again when you are ready to explore other terms."
        elif trigger == "COUNTER_OFFER_EXPIRED":
            reason = "The proposed counter-offer has expired."
            advice = "Please start a new application to see your current options."
        elif trigger == "REPROMPT_TIMEOUT_EXPIRED":
            reason = "We did not receive the required information in time."
            advice = "Please start a new application when you have the information ready."

        return DecisionExplanation(
            rejection_details=RejectionDetails(
                reason=reason,
                actionable_advice=advice
            )
        )

    elif state == "PENDING_REPROMPT":
        return DecisionExplanation(
            reprompt_requirements=RepromptRequirements(
                missing_fields=["secondary_contact_number"],
                instructions="We couldn't reach your primary number. Please provide an active alternate phone number so we can complete your application."
            )
        )

    # For all other states (INTAKE, TRIAGE, PENDING_VERIFICATION, VERIFIED, OPTIMIZATION), 
    # we do not return a specific explanation payload.
    return None
