# Person A Architecture Challenge
**Date:** 2026-06-11
**Auditor:** Independent Architecture Review Board

---

## The Challenge
*Assumption to attack:* "RiskIntel requires a Machine Learning model to determine credit eligibility."

In enterprise banking and microfinance, ML is often a solution in search of a problem. Microfinance underwriting is fundamentally a deterministic exercise evaluating repayment capacity, household debt burdens, and basic credit history. 

Attempting to force an ML model into this space without a massive, proprietary, high-quality dataset leads to hallucinated logic, target leakage, and regulatory failure (as seen with E1). 

---

## 1. Evaluation of Options

### Option A: Train a new ML Eligibility Model using the "Best Available" Public Dataset
*The strategy: Find the least-bad public dataset (e.g., Loan_Default1) and train an XGBoost or Random Forest model.*

1. **Domain correctness:** **Low.** The best public datasets are inevitably U.S. mortgage or prime lending data. 
2. **Explainability:** **Medium.** Requires complex SHAP/LIME integrations which are computationally expensive and often confusing to end-users.
3. **Regulatory defensibility:** **Zero.** Bank regulators will fail any model trained on anonymous Kaggle data with mismatched domain features.
4. **Data requirements:** **Extreme.** Requires thousands of rows of perfectly clean, target-verified data.
5. **Resume value:** **High.** Demonstrates end-to-end MLOps pipeline construction.
6. **Demo value:** **Medium.** It's hard to visually demonstrate a backend ML model; the UI just shows a percentage.
7. **Engineering effort:** **Very High.** Requires model registries, drift monitoring, and complex data scaling pipelines.
8. **Risk of failure:** **Critical.** High probability of deploying a model that makes logically absurd, legally indefensible decisions.

### Option B: Fully Rule-Based Underwriting Scorecard (No ML)
*The strategy: Build an eligibility engine identical in philosophy to the Person B Readiness Engine (E5). Hardcode RBI/MFIN guidelines (e.g., FOIR limits, CIBIL thresholds).*

1. **Domain correctness:** **Perfect.** Reflects exactly how real Indian microfinance institutions operate on the ground.
2. **Explainability:** **Perfect.** 100% deterministic. You can point to the exact line of code or policy that drove the decision.
3. **Regulatory defensibility:** **Perfect.** Regulators love transparent, policy-backed scorecard grids.
4. **Data requirements:** **Zero.** Relies entirely on expert heuristics and published policy.
5. **Resume value:** **Medium.** Shows strong product and domain knowledge, but lacks "AI" buzzwords.
6. **Demo value:** **High.** Extremely predictable during live demos (no unpredictable ML hallucinations).
7. **Engineering effort:** **Low.** Simple mathematical weighted sums and boolean gates.
8. **Risk of failure:** **Zero.** 

### Option C: Hybrid Architecture
*The strategy: Use a rule-based scorecard for the actual approval/rejection gateway. Limit ML to non-gating functions like borrower segmentation (Archetypes), unstructured data processing, or generative coaching recommendations.*

1. **Domain correctness:** **High.** The gating decision is safely rooted in domain reality.
2. **Explainability:** **High.** The decision is deterministic; the ML just explains the "why" or "how to improve".
3. **Regulatory defensibility:** **High.** The ML does not make the credit decision, bypassing strict Model Risk Management (MRM) scrutiny.
4. **Data requirements:** **Low/Medium.** ML segmentation or generative AI does not require proprietary default datasets.
5. **Resume value:** **Extremely High.** Demonstrates "Responsible AI"—using ML for insights while putting strict deterministic guardrails on decisioning. This is exactly what enterprise companies are currently trying to figure out.
6. **Demo value:** **Very High.** Combines the bulletproof reliability of rules with the slickness of AI coaching.
7. **Engineering effort:** **Medium.**
8. **Risk of failure:** **Low.** If the ML fails, the system falls back to the deterministic decision.

---

## 2. Challenging the ML Assumption

**Why did we assume Person A needed an ML model in the first place?**
Usually, it is to satisfy a "Machine Learning" requirement for a hackathon, resume, or portfolio. However, using ML to make binary credit decisions on 10 input variables is mathematically inferior to a well-designed expert scorecard, especially when the training data is anonymous or synthetically contaminated. 

An ML model is a black box that approximates the rules of the universe based on historical data. If you already *know* the rules of the universe (e.g., MFIN says household debt cannot exceed 50% of income), using an ML model to "discover" that rule is an unnecessary architectural risk.

---

## 3. Final Recommendation

**Recommend: Option B (with an Option C future path).**

RiskIntel should immediately adopt **Option B** for the Person A Eligibility Engine.

1. **Demote the E1 ML Pipeline:** Delete the scikit-learn models, the pickling pipelines, and the SHAP explainers.
2. **Replicate the E5 Architecture:** Build a `PersonA_Eligibility_Scorecard` that mirrors the deterministic brilliance of the Person B Readiness Engine. 
3. **The Smallest Architecture:** A scorecard requires zero data sourcing, zero model training, zero drift monitoring, and zero fear of target leakage. It will pass any banking audit instantly.
4. **Delivering the Mission:** The mission of RiskIntel is *Explainable AI underwriting*. The intelligence does not have to be in the *approval decision*. The AI value proposition is in the **Recommendation Engine (E4)**—the way the system intelligently coaches the borrower. 

By dropping the requirement for a proprietary ML training dataset, we remove the single largest blocker to shipping a mathematically defensible, production-ready system.
