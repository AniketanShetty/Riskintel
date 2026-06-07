# RiskIntel — Thin-File Evaluation Policy

**Date:** 2026-06-07
**Status:** Binding Model Risk and Product Policy

## 1. Current V1 Policy

In V1, RiskIntel explicitly separates borrowers with a valid credit history (Person A) from first-time or thin-file borrowers (Person B).

- **What thin-file borrowers are assessed by today:** The E5 Readiness Engine (a hand-coded, deterministic 0-100 heuristic) and the E6 Livelihood Engine (a dictionary lookup).
- **Which E5 factors remain active:** All original V1 factors remain active to ensure the engine functions: Financial Health (35%), Housing Stability (20%), Infrastructure Access (15%), Household Burden (15%), and Business Viability (15%). A hard policy floor override forces a "Not Ready" band if Financial Health drops below 0.5.
- **Which factors are removed or modified:** None are removed from the E5 algorithm in V1. However, the system's routing layer has been modified to eliminate silent rerouting and ensure E3 (Archetype) and E1 (Eligibility) are never executed for a thin-file borrower. E5 requires metadata injection (`last_reviewed_at`, `reviewed_by`).
- **What messages the borrower sees:** *"Because you do not have a standard credit history in our system, we assessed your readiness based on your income, expenses, and business setup. Your readiness score is [Score], placing you in the [Band] band. This is a readiness assessment, not a formal credit score approval."*
- **What the employee sees:** The Readiness Score (0-100), the Readiness Band, explicit policy override flags (e.g., Financial Health floor breach), and an `is_unclassified` boolean flag from E6 if the business type is unknown.
- **What gets audited:** Every assessment attempt. The `audit_log` records `correlation_id`, the explicit `routing_decision` (e.g., `routed_to: person_b`), engine execution statuses, policy override flags, and any unhandled exceptions.

## 2. V2 Redesign Proposal

While E5 functions deterministically, its current weights are based on author intuition and encode systemic poverty proxies. A V2 redesign is required to make the framework fully defensible.

- **How the framework would be improved:** V2 will shift to an additive, proxy-free, cash-flow-centric model. Borrowers will earn points for verifiable positive signals (e.g., business tenure, cash-flow surplus) rather than starting at 100 and being penalized for demographic realities.
- **Which poverty proxies should be reduced or removed:** Infrastructure Access (water/sanitation) and Physical Housing Construction (Kucha/Pucca material) must be completely removed, as they penalize municipal failures and regional poverty rather than individual repayment capacity.
- **Which factors should be reweighted or replaced:** Housing Stability must shift from construction material to *residential tenure* (time at address). Financial Health must shift to an explicit Income-to-Expense ratio.
- **What fairness testing would be required:** Before adoption, V2 must pass disparate-impact testing ensuring rural, low-income, and female borrowers are not disproportionately penalized by the chosen scoring logic compared to urban or formal-sector borrowers.

## 3. Non-Negotiable Rules

1. **No silent rerouting:** Missing or sentinel CIBIL scores (0/-1) must explicitly log a `routing_decision` and notify the caller.
2. **No approval probability for thin-file borrowers:** The system outputs a Readiness Band, never a calibrated probability of default or approval.
3. **No E3 archetype for thin-file borrowers:** The broken E3 KMeans model must never execute for Person B.
4. **No claim that the system is an autonomous credit decisioning AI:** It is a heuristic decision-support tool.

## 4. Decision Boundary

To clarify what developers and risk officers must build today versus plan for tomorrow, all proposed improvements are classified below:

| Proposed Improvement | Classification | Reason |
|---|---|---|
| Explicit `routing_decision` in API payload | **V1 Immediate** | Required to fix silent rerouting audit failure. |
| Add rule-review metadata to E5 outputs | **V1 Immediate** | Required to make E5 rule policy auditable. |
| Remove Infrastructure from E5 scoring | **V2 Future** | Requires a full engine rebuild; currently blocked by V1 stability needs. |
| Shift Housing Stability to Residential Tenure | **V2 Future** | Requires new frontend/data inputs not present in V1. |
| Add `is_unclassified` flag to E6 | **V1 Immediate** | Required to prevent silent business-type failures. |
| Use Machine Learning for Person B Scoring | **Rejected** | Thin-file borrowers lack the target labels required to train a fair ML model without proxy discrimination. |

## 5. Do we change E5 now?

**No.**

The audited reality confirms that E5 is a rule-based, deterministic heuristic and is the *only* defensible thin-file engine currently available to the organization. While its reliance on infrastructure proxies is a fairness risk, removing or modifying the E5 algorithm now would break the system's ability to assess Person B borrowers entirely. For V1, we **KEEP E5 as-is**, add rule-review documentation, surface the routing decisions explicitly, and enforce strict fail-closed audit logging. The V2 redesign remains a strictly future initiative.
