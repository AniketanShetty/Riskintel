# RiskIntel V2: Application Flow (State Machine)

## 1. Global State DAG
*Source: `STATE_MACHINE.md`, `ADR-023`, `ADR-025`*

```mermaid
stateDiagram-v2
    [*] --> INTAKE
    INTAKE --> TRIAGE : 5_question_floor_submitted
    
    TRIAGE --> PENDING_VERIFICATION : triage_math_pass
    TRIAGE --> NOT_READY_YET : triage_math_fail
    
    PENDING_VERIFICATION --> PENDING_REPROMPT : missing_secondary_contact
    PENDING_REPROMPT --> PENDING_VERIFICATION : reprompt_submission_received
    PENDING_REPROMPT --> NOT_READY_YET : reprompt_timeout_expired
    
    PENDING_VERIFICATION --> VERIFIED : verification_success
    PENDING_VERIFICATION --> NOT_READY_YET : fraud_detected / max_retries
    
    VERIFIED --> OPTIMIZATION : optimization_trigger
    
    OPTIMIZATION --> READY : target_met
    OPTIMIZATION --> NEARLY_READY : alternative_counter_offer_generated
    OPTIMIZATION --> NOT_READY_YET : hard_block_math_failure
    
    NEARLY_READY --> PENDING_VERIFICATION : user_submits_coapplicant
    NEARLY_READY --> READY : user_accepts_counter_offer
    NEARLY_READY --> NOT_READY_YET : user_rejects_counter_offer / timeout
    
    READY --> [*]
    NOT_READY_YET --> [*]
```

## 2. Recovery Loops (The Cyclic Exceptions)
The architecture explicitly bans loops to prevent infinite logic execution, with exactly two mathematically bounded exceptions:

1.  **The Re-Prompt Loop (`PENDING_REPROMPT` -> `PENDING_VERIFICATION`):** Solves field officer omissions without failing the borrower. Bounded by a strict TTL timeout.
2.  **The Co-Applicant Loop (`NEARLY_READY` -> `PENDING_VERIFICATION`):** Allows a failed Primary Applicant to append household income and restart the verification freeze. Bounded by state constraints.
