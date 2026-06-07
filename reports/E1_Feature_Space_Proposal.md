# E1 Feature Space Re-engineering Proposal

**Role:** Principal Data Scientist  
**Objective:** Redesign the E1 feature space to support a genuinely multivariate predictive risk model, eliminating the single-feature dominance of the `cibil_score`.

## Current Feature Deficiencies
The existing features (`cibil_score`, `income`, `assets`, `loan amount`, `tenure`) failed to produce a multivariate model because the target labels were deterministically bound to the credit score. To build a true risk model, we must predict an organic default label (e.g., *90-days past due within 12 months*) using features that capture an applicant's *capacity* and *character* orthogonal to the lagging indicator of a credit bureau score.

---

## Proposed Feature Space (Ranked)

### Tier 1: Highest Predictive Value & Highest Regulatory Safety
*These features are explicitly tied to the applicant's mathematical ability to repay (Capacity) and are highly defensible under fair lending laws (ECOA).*

**1. Derived Ratios (Capacity)**
*   **Debt-to-Income (DTI) / Fixed Obligations to Income Ratio (FOIR):** The definitive measure of financial bandwidth. (Total monthly debt payments / Gross monthly income).
*   **Payment-to-Income (PTI):** (Proposed Loan EMI / Net Monthly Income). 
*   **Asset-to-Loan Ratio:** Liquid assets divided by the requested loan amount. Represents the primary buffer against shock.

**2. Cash-Flow Features (via Open Banking / Bank Statement Parsing)**
*   **Net Free Cash Flow:** (Total Monthly Inflows - Non-Discretionary Outflows). Unlike gross income, this measures actual liquidity available to service a new loan.
*   **NSF Event Frequency:** Count of Non-Sufficient Funds or overdraft events in the trailing 90 days. Highly predictive of immediate financial distress.
*   **End-of-Month (EOM) Liquidity Margin:** Average balance remaining in the primary checking account on the day before the next payroll deposit.

### Tier 2: High Predictive Value & Moderate Regulatory Safety
*These behavioral features are excellent risk predictors but require disparate impact testing to ensure they do not unintentionally proxy for protected classes (e.g., penalizing gig economy workers).*

**3. Behavioral Features (Velocity & Trend)**
*   **Credit Utilization Trajectory:** Is the applicant's credit utilization increasing, stable, or decreasing over the last 6 months? (Velocity is often more predictive than the absolute percentage).
*   **Income Volatility Index:** The coefficient of variation in monthly inflows. High volatility indicates unstable earning capacity.
*   **Minimum Payment Behavior:** Ratio of credit card tradelines where only the minimum payment was made over the last 3 statement cycles.

**4. Advanced Risk Indicators**
*   **Recent Credit Seeking Velocity:** Number of hard inquiries in the trailing 30 vs. 90 days. Indicates "credit shopping" or acute desperation.
*   **Tradeline Maturity:** Average age of open credit accounts. Demonstrates long-term stability orthogonal to the raw credit score.
*   **Delinquency Recency:** Days since the most recent 30-day late payment.

### Tier 3: Alternative Data Sources (High Value, High Implementation Complexity)
*For applicants with "thin files" (little to no CIBIL history), alternative data provides the missing signal.*

**5. Alternative Data**
*   **Telecom / Utility Payment History:** Consistent payment of recurring telecom or utility bills. Highly safe regulatorily as it serves as a proxy for financial responsibility for unbanked populations.
*   **Rental Payment History:** Verification of consistent rent payments via property management APIs. 

---

## Architectural Implementation Roadmap

To execute this feature space:

1.  **Organic Labels:** We must stop predicting synthetic "Eligibility" labels. We must train the new model on historical data predicting actual, organic default events (e.g., `Default_90_DPD`).
2.  **Open Banking Integration:** Features in Tier 1 & 2 require granular transactional data. We must integrate with a banking aggregator API (e.g., Plaid, Finicity, Account Aggregator framework).
3.  **Orthogonality Testing:** Before finalizing the model, we must run correlation matrices and Variance Inflation Factor (VIF) analyses to ensure these new features are not highly collinear with the `cibil_score`. We want a model that learns *new* risk topologies, not one that re-learns the credit score through proxies.
