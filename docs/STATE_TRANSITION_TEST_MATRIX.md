# RiskIntel V2: State Transition Test Matrix

This matrix provides an exhaustive mapping of every allowed event, transition, and output for the 8 core states in the RiskIntel V2 architecture.

---

### 1. INTAKE

| Parameter | Details |
| :--- | :--- |
| **State** | `INTAKE` |
| **Allowed Events** | `submit_5_question_floor`, `abort_application` |
| **Allowed Transitions** | `TRIAGE` |
| **Forbidden Transitions** | `PENDING_VERIFICATION`, `VERIFIED`, `OPTIMIZATION`, `READY`, `NEARLY_READY`, `NOT_READY_YET` |
| **Expected Output** | Triggers Triage Engine evaluation. Validates PAN/Aadhaar syntax. |

---

### 2. TRIAGE

| Parameter | Details |
| :--- | :--- |
| **State** | `TRIAGE` |
| **Allowed Events** | `triage_math_pass`, `triage_math_fail`, `bureau_trust_fail` |
| **Allowed Transitions** | `PENDING_VERIFICATION`, `NOT_READY_YET` |
| **Forbidden Transitions** | `INTAKE`, `VERIFIED`, `OPTIMIZATION`, `READY`, `NEARLY_READY` |
| **Expected Output** | Upper-bound capacity generated. Routes applicant to verification pipeline or halts application instantly on hard bureau rules. |

---

### 3. PENDING_VERIFICATION

| Parameter | Details |
| :--- | :--- |
| **State** | `PENDING_VERIFICATION` |
| **Allowed Events** | `aa_success`, `fo_verified_clean`, `fo_verified_with_variance`, `fo_fraud_detected`, `unreachable_max_retries`, `user_refusal` |
| **Allowed Transitions** | `VERIFIED`, `NOT_READY_YET` |
| **Forbidden Transitions** | `INTAKE`, `TRIAGE`, `OPTIMIZATION`, `READY`, `NEARLY_READY` |
| **Expected Output** | Optimization Engine is strictly frozen. State holds until a verified payload is received or terminal failure occurs. |

---

### 4. VERIFIED

| Parameter | Details |
| :--- | :--- |
| **State** | `VERIFIED` |
| **Allowed Events** | `verification_payload_processed` (Internal Auto-Trigger) |
| **Allowed Transitions** | `OPTIMIZATION` |
| **Forbidden Transitions** | `INTAKE`, `TRIAGE`, `PENDING_VERIFICATION`, `READY`, `NEARLY_READY`, `NOT_READY_YET` |
| **Expected Output** | Categorical intake constraints are permanently destroyed. Exact integers are locked into memory. Automatically triggers Optimization. |

---

### 5. OPTIMIZATION

| Parameter | Details |
| :--- | :--- |
| **State** | `OPTIMIZATION` |
| **Allowed Events** | `affordability_target_met`, `affordability_alternative_found`, `math_wall_hit` |
| **Allowed Transitions** | `READY`, `NEARLY_READY`, `NOT_READY_YET` |
| **Forbidden Transitions** | `INTAKE`, `TRIAGE`, `PENDING_VERIFICATION`, `VERIFIED` |
| **Expected Output** | Exact Target EMI calculated. Tenure / Loan Amount levers executed. Final architectural output generated. |

---

### 6. READY

| Parameter | Details |
| :--- | :--- |
| **State** | `READY` |
| **Allowed Events** | `user_accepts_terms`, `user_declines_terms` |
| **Allowed Transitions** | `[*]` (Terminal) |
| **Forbidden Transitions** | Any reverse transition to `OPTIMIZATION`, `VERIFIED`, `PENDING_VERIFICATION`, `TRIAGE`, `INTAKE` |
| **Expected Output** | Celebration UI. Triggers disbursement sequence and contract generation. |

---

### 7. NEARLY_READY

| Parameter | Details |
| :--- | :--- |
| **State** | `NEARLY_READY` |
| **Allowed Events** | `user_submits_coapplicant`, `user_accepts_counter_offer`, `user_rejects_counter_offer`, `counter_offer_expired` |
| **Allowed Transitions** | `PENDING_VERIFICATION`, `READY`, `NOT_READY_YET` |
| **Forbidden Transitions** | Unilateral transition to `READY` without explicit event. Transition to `OPTIMIZATION`. |
| **Expected Output** | Cyclic recovery loop activated. Wait for formal user interaction with counter-offer UI or dual-track payload. |

---

### 8. NOT_READY_YET

| Parameter | Details |
| :--- | :--- |
| **State** | `NOT_READY_YET` |
| **Allowed Events** | `user_reads_roadmap` |
| **Allowed Transitions** | `[*]` (Terminal) |
| **Forbidden Transitions** | Any forward transition. It is the absolute end of the application loop. |
| **Expected Output** | Recovery roadmap UX detailing the exact failure point (Trust, Affordability, Verification, Resilience). |
