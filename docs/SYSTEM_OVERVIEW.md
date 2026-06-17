# System Overview

## What RiskIntel Solves

RiskIntel V2 is a deterministic, highly bounded loan decision orchestration platform. It is designed to replace traditional, opaque Machine Learning scoring models with a transparent Finite State Machine (FSM).

The primary goal of RiskIntel is to process loan applications safely and fairly, ensuring that applicants are never placed in unserviceable debt. By utilizing strict mathematical bounds, the system evaluates affordability, filters through external verifications, and calculates optimal counter-offers without relying on probabilistic "black box" algorithms.

## Core Concepts

1. **Deterministic State Machine:** Every loan application is bound to a strict chronological lifecycle. Applicants cannot skip states, and external verifications (e.g., from Account Aggregators or Field Officers) are rejected if the applicant is not in the appropriate state.
2. **Mathematical Optimization:** Rather than a simple "Pass/Fail" based on a credit score, RiskIntel calculates maximum affordable capacity. If a user requests a loan that exceeds their capacity, the system algebraically calculates a counter-offer by stretching the loan tenure up to the absolute limit.
3. **Cyclic Recovery Loops:** To maximize financial inclusion, RiskIntel actively attempts to rescue failing applications. If an applicant has a "thin" credit file, they are prompted to submit a Co-Applicant. If verifications are blurry or incomplete, the system enters a reprompt loop rather than issuing a flat rejection.
4. **Idempotent Operations:** In distributed fintech environments, network retries are common. RiskIntel utilizes robust idempotency keys to guarantee that a network retry never results in duplicate loans or corrupted states.

## User Journey

The standard RiskIntel V2 lifecycle follows this sequence:

1. **Intake:** The applicant submits their initial data (Income Bracket, Desired Loan Amount, Pincode). The system creates an application session.
2. **Triage:** The system performs lightweight mathematical affordability checks to determine if the user has any mathematical chance of affording the loan based on basic poverty line calculations.
3. **External Verification:**
   * The application enters the `PENDING_VERIFICATION` state.
   * Asynchronous webhooks receive definitive financial data from Account Aggregators (AA) and physical site checks from Field Officers (FO).
4. **Optimization:** Once fully verified, the system's mathematical engine determines the exact debt-to-income limits.
   * If the loan fits entirely within bounds, the applicant becomes `READY`.
   * If the loan exceeds bounds, the engine stretches the tenure to propose a counter-offer (`NEARLY_READY`).
   * If even at the maximum tenure the loan is unaffordable, the applicant is `REJECTED`.
5. **Decision:** The applicant explicitly accepts or rejects any counter-offers.
