# Livelihood Resilience: Evidence-Based Framework
**Date:** 2026-06-11

---

## 1. The Fallacy of Occupation Labels
Assigning risk scores based on occupation labels (`Farmer = X`, `Driver = Y`, `Tailor = Z`) is fundamentally flawed. It relies on macro-stereotypes rather than individual borrower behavior, leading to severe Disparate Impact (fair lending violations). A highly experienced Swiggy driver with a 4.9 rating and 3 years of tenure is mathematically less risky than a tailor who opened their shop last week, despite the "Tailor" occupation traditionally carrying higher prestige in banking software.

To achieve true, unbiased underwriting, **Livelihood Resilience must be based exclusively on observable, structural evidence of cash-flow durability.**

---

## 2. Observable Evidence Vectors

Instead of asking "What do you do?", the system evaluates "How resilient is the way you earn money?" using five structural vectors:

### A. Income Diversification
*   **The Evidence:** Does the household rely on a single point of failure?
*   **Observable Metrics:** 
    *   Presence of Secondary Household Income (Declared in triage or observed via co-applicant).
    *   Off-season income (e.g., a farmer who also runs a dairy/poultry operation).
*   **Optimization Lever:** If this score is low, the engine recommends adding a co-applicant.

### B. Revenue Consistency (The "Repeat" Factor)
*   **The Evidence:** Is every day a hunt for new customers, or is there a baseline of predictable revenue?
*   **Observable Metrics:**
    *   *Digital Trace:* UPI Merchant history showing repeat QR code scans from the same sender IDs.
    *   *Platform Trace:* Gig worker metrics (e.g., number of completed rides/deliveries per week).
    *   *Manual Trace:* Physical field visit verifying an active ledger book (Khata) or fixed client contracts.

### C. Structural Vintage (Tenure)
*   **The Evidence:** Has this livelihood survived a full economic cycle (or at least a full year of seasonal shifts)?
*   **Observable Metrics:**
    *   *Gig Workers:* Date of onboarding onto the digital platform (Uber/Swiggy API).
    *   *Business Owners:* Date of GST registration, Udyam Aadhar, or shop lease agreement.
    *   *Farmers:* Number of consecutive crop cycles on the same land.

### D. Volatility / Seasonality
*   **The Evidence:** Does the income completely disappear for months at a time?
*   **Observable Metrics:**
    *   Account Aggregator / Bank Statement variance. (e.g., Are deposits clustered entirely in April and November for harvest seasons, or is there a monthly baseline?)

---

## 3. Scoring Matrix (No Labels Required)

By shifting to this framework, the borrower's occupation label becomes irrelevant for the risk calculation (it is only used to customize the UX phrasing of the questions). 

**The Universal Resilience Score:**
1.  **High Resilience (Green):** Multi-stream income OR single-stream with >2 years verifiable vintage and low monthly volatility.
2.  **Moderate Resilience (Yellow):** Single-stream income with <1 year vintage, but highly verifiable repeat-customer behavior / platform metrics.
3.  **Low Resilience (Red):** Single-stream, high-volatility income with no verifiable vintage or secondary support (e.g., a daily wage laborer who just moved to a new city last week).

### Why this is Architecturally Superior:
1.  **Anti-Bias:** It mathematically removes elitism. A street vendor with 3 years of verifiable UPI merchant history will easily outscore a failing tech startup founder.
2.  **API Compatible:** Metrics like "Platform Tenure" and "Repeat UPI Customers" can be scraped directly from Account Aggregators or specialized APIs, requiring zero typing from the user.
3.  **Actionable Coaching:** If a borrower gets a Low Resilience score, the feedback is highly specific: *"Your business income is currently too volatile for this loan amount. Adding a co-borrower with salaried income will instantly boost your Resilience Score to the approval tier."*
