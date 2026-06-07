# RiskIntel Task — Thin-File Borrower Evaluation Framework

## Constitution Check
RiskIntel exists to:
1. Give borrowers transparent and fair assessments (explicit eligibility/readiness, plain-language reasons, no silent rerouting).
2. Give loan officers structured reports that reduce manual work and ensure a consistent review workflow.

---

## 1. What should a fair thin-file assessment try to measure?
A fair thin-file assessment cannot rely on historical credit behavior. Instead, it must measure current capacity and stability through five distinct lenses:
- **Willingness to repay:** Behavioral indicators that demonstrate financial discipline and intent to honor obligations (e.g., regularity of utility payments, consistent savings habits).
- **Ability to repay:** The quantitative, mathematical capacity to service new debt (calculated via the ratio of verified income against fixed living expenses and existing informal debt).
- **Business stability:** The operational viability, tenure, and market alignment of the borrower's micro-enterprise or livelihood.
- **Household resilience:** The capacity of the borrower's household to absorb sudden economic shocks (e.g., medical emergencies, crop failure) without defaulting, often measured by secondary income sources or the dependent-to-earner ratio.
- **Documentation quality:** The presence of verifiable KYC, business registration, or alternative data that formalizes the borrower's identity and operational footprint.

## 2. Which factors should matter?

| Factor | Rationale | Fairness Risk | Explainability | Borrower Improvable? |
|---|---|---|---|---|
| **Income-to-Expense Ratio** | Direct measure of surplus cash flow and capacity to repay. | Low (Purely mathematical). | High | Yes (By increasing revenue or cutting expenses). |
| **Business Tenure** | Businesses that have survived longer are statistically more resilient to shocks. | Low | High | Yes (By maintaining operations over time). |
| **Savings Regularity** | A proxy for financial discipline and willingness to repay. | Medium (Banks must accept informal savings/chit funds, not just formal bank statements). | High | Yes (By establishing regular savings habits). |
| **Dependent-to-Earner Ratio** | Measures household economic burden and resilience. | Medium (May penalize larger, traditional families). | High | No (Demographic reality). |
| **Loan Purpose Alignment** | Ensures the capital is used productively (e.g., buying inventory for a retail shop) rather than for consumptive mismatch. | Low | High | Yes (By aligning request with core business). |

## 3. Which factors should NOT matter?
- **Caste, Religion, Gender:** Strictly prohibited by law and ethics. Using these factors guarantees redlining and illegal proxy discrimination.
- **Physical House Construction (Pucca/Kucha):** Highly correlated with systemic, historical, and regional poverty. The material of a borrower's roof does not dictate the cash-flow viability of their tailoring business.
- **Municipal Infrastructure (Water/Sanitation):** Penalizes the borrower for municipal or governmental failures. Access to piped water is not a reliable proxy for individual repayment intent.

## 4. Which current E5 factors should remain?

- **Financial Health:** **KEEP AND REFINE.** It directly measures the ability to repay. Refine to focus purely on cash-flow ratios rather than absolute income floors.
- **Housing Stability:** **MODIFY.** Remove the strict scoring penalties for "Kucha" or "T2" housing types. Shift the focus entirely to *tenure* at the current residence (stability) rather than construction material (wealth proxy).
- **Infrastructure Access:** **REMOVE.** As noted above, penalizing a lack of sanitation or piped water is a proxy for systemic poverty and fails disparate-impact tests.
- **Household Burden:** **MODIFY.** Focus purely on the economic dependency ratio rather than penalizing absolute family size.
- **Business Viability:** **KEEP AND REFINE.** Ensure the livelihood mapper (E6) evaluates the alignment between the requested loan purpose and the primary business type.

## 5. Propose a replacement scoring framework
**Principles:**
- **Additive, not Deductive:** Borrowers start at zero and earn points for verifiable positive signals (e.g., +20 for 3 years business tenure), rather than starting at 100 and being penalized for poverty markers.
- **Proxy-Free:** Exclude all variables correlated with protected classes or systemic regional poverty.
- **Cash-Flow Centric:** Emphasize the mathematical ability to repay over asset wealth.

**Policy Logic & Scoring Philosophy:**
The score does not represent an "approval probability." It is a **Readiness Tier** (0-100) mapped directly to risk-mitigation strategies. A lower score does not mean "Reject"; it means "Require a co-signer," "Reduce loan principal," or "Require weekly instead of monthly collections."

**Defensibility:** A loan officer can defend this framework because it is tied directly to the borrower's documented cash-flow surplus and business tenure, rather than arbitrary 15% weights on infrastructure availability.

## 6. Borrower Explainability
- **Income-to-Expense Ratio:** *"Your readiness score is strong because your monthly business income comfortably covers your current living expenses and the proposed loan payment."*
- **Business Tenure:** *"Your score improved because you have operated your business for over three years, showing stability."*
- **Household Burden:** *"Your readiness score was reduced because a large portion of your income must currently support dependents, leaving less room for new loan payments."*
- **Loan Purpose Alignment:** *"Your score was impacted because your requested loan purpose does not align with your primary business type, increasing the risk of the investment."*

## 7. Employee Utility
- **Branch Officers:** Quickly identifies cash-flow constraints and business alignment issues *before* the officer spends hours doing manual field verification.
- **Underwriters:** Provides a structured, standardized baseline for the borrower's actual capacity, replacing subjective "gut feelings" with reproducible metrics.
- **Auditors:** Offers full transparency into exactly why a thin-file borrower was recommended or flagged, without hidden ML weights or undocumented policy floors.

## 8. Fairness Analysis
- **Women Borrowers:** Often lack formal property titles or business registrations in their name. **Mitigation:** The framework must accept alternative, informal proofs of operation and residence tenure.
- **Rural Borrowers:** Heavily disadvantaged by infrastructure and housing type penalties. **Mitigation:** Infrastructure factors have been completely removed from the proposed framework.
- **Low-Income Borrowers:** Disadvantaged by strict income floors. **Mitigation:** The framework focuses on the *ratio* of surplus cash flow rather than absolute income volume.
- **First-Time Borrowers:** Disadvantaged by the lack of credit history. **Mitigation:** The additive scoring model builds a profile based on current operational realities and savings habits, not historical debt service.

## 9. Final Recommendation
**Redesign E5 entirely.**

The current E5 framework cannot be saved by simply tweaking the weights. It fundamentally relies on arbitrary author intuition and heavily penalizes systemic poverty (infrastructure, housing type) rather than assessing actual repayment capacity and business cash flow. An additive, cash-flow-centric model that removes poverty proxies is significantly more defensible, fair, and aligned with the RiskIntel constitution.
