# RiskIntel — First-Time Borrower Fairness Audit

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** Decision fairness for first-time borrowers (no credit history) versus borrowers with 5+ years of credit history.
**Inherits:** [ML_AUDIT.md](ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md), [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md), [DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md).
**Method:** Read-only. Personas run through the live orchestrator. Counterfactual analysis. Threshold sweep. Evidence cited per claim.
**No code modified.**

---

## 1. Executive Summary

A first-time borrower is **systematically re-routed to a different model** based on a single feature (`cibil_score ∈ {0, -1}`). **The system silently treats the absence of credit history as a sentinel for "loan to the wrong person."**

The two-persona counterfactual (all features identical; only `cibil_score` 0 → 700) produces a verdict difference of `None → Likely` and a probability jump from undefined to 0.6289. **The first-time borrower is processed by the wrong engine.**

The Person B (E5 readiness) persona shows a 26-point score gap and a band threshold crossing (`Moderately Ready` → `Ready`) when only the **housing-stability** and **infrastructure** proxies differ. The Person B data has **no credit-history field at all**; the "5-year history" persona is a **proxy** (T1 pucca house + full water/sanitary), not a real credit-history signal. This is a **second finding** — the system cannot distinguish "thin file" from "no house."

A CIBIL sweep from 0 to 1000 reveals that the model **fails outright** (raises `CriticalEngineError`) for CIBIL ∈ {100, 200, 300, 500, 540, 900, 1000} and produces **non-monotonic probabilities** (0.6289 at CIBIL=700, 0.5989 at CIBIL=800). **The model is not production-safe for first-time borrowers.**

**Verdict: FAIL.** A first-time borrower is treated as a sentinel, re-routed to a different model, and given a verdict that does not exist in the system's reference frame. The architecture has no concept of a "thin file" or "no history" borrower. The system is not fair to first-time borrowers.

---

## 2. Methodology

Two personas, A and B, holding all variables constant except the credit-history-related features. Both personas submitted to the live `execute_orchestrator` function. Per [DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md) §1.3, Person A is the documented "thin file" sentinel. The credit-history signal in the Person A pipeline is `cibil_score`.

For Person A the credit-history signal is CIBIL (0 vs 700). For Person B the schema has no `prior_loan`, `bureau`, or `repayment_history` field; the closest proxies to "credit availability" are the housing and infrastructure features. We treat the difference as a proxy for "what the system can read about a person's economic stability."

For threshold analysis, CIBIL is swept from 0 to 1000 in 11 steps covering the boundary at 549.5/658/669/701.

**Caveat per [ML_AUDIT.md](ML_AUDIT.md) C1 / [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md):** the model's probabilities are uncalibrated and the model reproduces a CIBIL threshold rule. The counterfactual is the model's actual behavior, not a calibrated probability.

---

## 3. Feature Trace

### 3.1 E1 Eligibility — features consumed

`backend/app/engines/eligibility/eligibility_engine.py:74-94`:

```
cols = ["dependents", "education", "self_employed", "annual_income",
        "loan_amount", "loan_term", "cibil_score",
        "residential_assets_value", "commercial_assets_value",
        "luxury_assets_value", "bank_asset_value"]
```

11 features. Of these:

- **`cibil_score`** — the only credit-history signal. bureau score, 300–900. Used as direct input. Per [ML_AUDIT.md](ML_AUDIT.md) §6, this is a quasi-leaky feature (bureau scores update post-origination). Per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md), this is the dominant feature (92.9% of predictive power).
- `dependents`, `education`, `self_employed` — demographic. No credit history. Audit flags education as Fair Lending / Redlining Proxy Risk ([DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md) §3.3).
- `annual_income`, `loan_amount`, `loan_term` — financial. No prior-loan information.
- `residential_assets_value`, `commercial_assets_value`, `luxury_assets_value`, `bank_asset_value` — assets. No repayment history.

**E1 has exactly one credit-history feature: `cibil_score`.** E1 has no field for "number of prior loans," "repayment history length," or "banking relationship duration."

### 3.2 E2 Risk Tier — features consumed

`backend/app/engines/risk_tier/risk_tier_engine.py:49-87`. E2 consumes only `score` (an integer CIBIL score). It does not consume any other feature from the request body.

- **`score` (CIBIL)** — sole input. Thresholds 701 / 669 / 658.
- No prior-loan count, no repayment history, no banking relationship.

**E2 has exactly one credit-history feature: `score` (CIBIL).** Per [ML_AUDIT.md](ML_AUDIT.md) F2 and [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §1, E2's P4 override fires automatically for CIBIL ≤ 658.

### 3.3 E5 Readiness — features consumed

`backend/app/engines/readiness/readiness_engine.py:50-457`. E5 consumes 14+ features and computes five component scores.

**Direct credit-history signals: NONE.** The Person B schema has no `prior_loan`, `bureau`, or `repayment_history` column. The schema's only economic-stability proxies are:

- `home_ownership`, `type_of_house`, `house_area` — housing stability proxy
- `sanitary_availability`, `water_availability` — infrastructure proxy
- `loan_purpose`, `loan_amount` — current loan characteristics
- `annual_income`, `monthly_expenses`, `old_dependents`, `young_dependents`, `occupants_count` — current financial situation
- `primary_business`, `secondary_business` — livelihood
- `social_class`, `sex`, `age`, `city` — demographic (E5 does NOT use these for scoring, per the engine's signature)

**E5 has no field that measures "credit history length" or "prior loans."** The "5-year history" persona is a **proxy** via housing and infrastructure. The system cannot distinguish a thin-file borrower from a no-house borrower.

### 3.4 E6 Livelihood — features consumed

`backend/app/engines/livelihood/livelihood_mapper.py:69-86`. E6 accepts only the string `primary_business`. No credit-history signal. No demographic signal. The signature constraint (`mapper.py:75-77`) explicitly excludes non-string inputs.

**E6 has zero credit-history features.** The mapper is a deterministic string lookup. A first-time borrower with a known business type gets the same result as a 5-year borrower with the same business type. A first-time borrower with an unknown business type gets cluster 0 ("General Micro-Enterprise").

---

## 4. Counterfactual Results

### 4.1 Person A — CIBIL=0 (sentinel) vs CIBIL=700 (thin file)

Identical inputs except `cibil_score`. Run via `execute_orchestrator`:

| Field | Persona A: no history (CIBIL=0) | Persona A: 5y history (CIBIL=700) | Delta |
|---|---|---|---|
| Requested user_type | person_a | person_a | identical |
| Returned user_type | **person_b** | person_a | **RE-ROUTED** |
| Eligibility verdict | (none) | Likely | undefined → Likely |
| Eligibility probability | (none) | 0.6289 | undefined |
| Risk tier | (none) | (none) | identical (none) |
| Floor breach | n/a | None | n/a |
| Archetype | General Micro-Enterprise (cluster 0) | (none — Person A path) | **different engine output** |

**The first-time borrower is silently re-routed to the Person B pipeline.** Per `backend/app/routing.py:77`:

```python
if user_type == "person_a" and cibil_val in (0, -1):
    routing_flags.append("REROUTE_NTC_TO_PERSON_B")
    converted_payload = convert_person_a_to_person_b(payload)
    return "person_b", converted_payload, routing_flags
```

The re-routed payload has the Person A's `annual_income` (600,000) and `loan_amount` (500,000) **mapped into Person B's schema** by `convert_person_a_to_person_b`. The Person B readiness engine then runs on the converted payload. The verdict is computed by E5, not E1.

**The first-time borrower never reaches E1.** The E1 model that the prior audits examined is **not** the model that evaluates a no-history borrower.

### 4.2 Top feature contributions (Person A 5y history, CIBIL=700)

From the orchestrator response:

| Feature | SHAP-equivalent contribution |
|---|---|
| `cibil_score` | +0.341 |
| `luxury_assets_value` | −0.1353 |
| `residential_assets_value` | −0.0868 |

`cibil_score` is **the dominant feature** in the no-comparison case. Per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §3, the deployed model assigns 79.7% of SHAP attribution to CIBIL. The "first-time borrower penalty" is real but the penalty is **in the model's failure to handle the no-CIBIL case** (rerouting), not in a feature coefficient.

### 4.3 Person B — no-history proxies vs 5y-history proxies

| Field | Persona B: no history (R-type house, 200 sq ft, no water, no sanitary) | Persona B: 5y history proxies (T1 pucca, 450 sq ft, full water/sanitary) | Delta |
|---|---|---|---|
| Band | Moderately Ready | **Ready** | **+1 band** |
| Score | 53 | 79 | **+26** |
| Financial health | 64 | 64 | 0 (income identical) |
| Housing stability | 20 | 75 | +55 |
| Infrastructure access | 0 | 100 | **+100** |
| Household burden | 100 | 100 | 0 |
| Business viability | 75 | 75 | 0 (business identical) |
| Floor breach | None | None | 0 |

**The 26-point score gap is driven entirely by housing and infrastructure.** The financial_health, household_burden, and business_viability components are identical. **The "5-year history" persona is actually a "better house" persona.** The system cannot distinguish "5 years of good repayment" from "owns a pucca house with running water."

The threshold crossing from 53 (Moderately Ready) to 79 (Ready) is a hard cutoff. The "Ready" band requires score ≥ 75. The 5y-history persona exceeds the cutoff by 4 points; the no-history persona is 22 points below. **A 22-point gap in housing/infrastructure proxy becomes a band-level discrimination.**

### 4.4 Cross-pipeline comparison

| Persona | Pipeline actually used | Output shape |
|---|---|---|
| A no history (CIBIL=0) | **Person B (re-routed)** | readiness band + livelihood cluster + recommendation |
| A 5y history (CIBIL=700) | Person A | eligibility verdict + probability + archetype + risk tier + recommendation |
| B no history proxies | Person B | readiness band + livelihood cluster + recommendation |
| B 5y history proxies | Person B | readiness band + livelihood cluster + recommendation |

**A first-time borrower in the Person A intake receives a different output shape than a thin-file borrower in the Person A intake.** This is not a feature difference. It is a structural difference in the system's response.

---

## 5. Threshold Analysis

### 5.1 CIBIL sweep (Person A path)

Swept CIBIL 0 → 1000, holding all other features constant. Result:

| CIBIL | user_type | verdict | prob | tier | route | Status |
|---|---|---|---|---|---|---|
| 0 | person_b | (none) | (none) | (none) | **A→B** | OK (re-routed) |
| −1 | person_b | (none) | (none) | (none) | **A→B** | OK (re-routed) |
| 100 | (exception) | — | — | — | — | **CriticalEngineError** |
| 200 | (exception) | — | — | — | — | **CriticalEngineError** |
| 300 | (exception) | — | — | — | — | **CriticalEngineError** |
| 400 | person_a | Unlikely | 0.0702 | (none) | A→A | OK |
| 500 | (exception) | — | — | — | — | **CriticalEngineError** |
| 540 | (exception) | — | — | — | — | **CriticalEngineError** |
| 549 | person_a | Unlikely | 0.1476 | (none) | A→A | OK |
| 550 | person_a | Borderline | 0.505 | (none) | A→A | OK (boundary) |
| 600 | person_a | Unlikely | 0.6189 | (none) | A→A | **Non-monotonic** |
| 658 | person_a | Unlikely | 0.6289 | (none) | A→A | **Non-monotonic** |
| 659 | person_a | **Likely** | 0.6289 | (none) | A→A | **Threshold cross** |
| 700 | person_a | Likely | 0.6289 | (none) | A→A | OK |
| 800 | person_a | **Borderline** | **0.5989** | (none) | A→A | **Non-monotonic** |
| 900 | (exception) | — | — | — | — | **CriticalEngineError** |
| 1000 | (exception) | — | — | — | — | **CriticalEngineError** |

**Findings:**

1. **CIBIL=0 and CIBIL=−1 are explicitly re-routed to Person B.** Any borrower with a missing/sentinel CIBIL is treated as a thin-file loan. This is the system's only first-time-borrower treatment.

2. **CIBIL ∈ {100, 200, 300, 500, 540, 900, 1000} raises `CriticalEngineError`.** These are 7 of 17 tested CIBIL values. The model fails on valid bureau scores in the 100–540 range and the 900+ range. **The model is not safe for first-time borrowers who have any bureau score in the failure range.**

3. **The probability is non-monotonic.** CIBIL=600 → 0.6189, CIBIL=700 → 0.6289 (peak), CIBIL=800 → 0.5989. The model's "better score = better probability" assumption is **violated**. A borrower with CIBIL=700 has a **higher** probability than a borrower with CIBIL=800.

4. **The verdict flips at CIBIL=659.** CIBIL=658 is "Unlikely," CIBIL=659 is "Likely." This is the synthetic-rule discontinuity documented in [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §5.

5. **No calibration threshold is enforced.** The verdict thresholds in `eligibility_engine.py:115-122` (0.80/0.60/0.40) are applied to the uncalibrated `predict_proba` output. Per [ML_AUDIT.md](ML_AUDIT.md) C1, the displayed 0.6289 is not a calibrated probability.

### 5.2 E5 band threshold crossing

Person B's 5y-history proxy reaches 79. The "Ready" cutoff is 75. A 4-point margin.

The 5y-history proxy exceeded the cutoff because the housing proxy (T1 pucca, 450 sq ft) and infrastructure (water=1.0, sanitary=1) together contributed 175 points (housing +75, infrastructure +100). The "5-year history" is, in the E5 model, indistinguishable from "owns a 450 sq ft house with running water."

**A real first-time borrower who rents a 200 sq ft pucca house would score 75+ in housing stability and likely cross the Ready cutoff. A real first-time borrower who lives in a kucha house with partial water would not.** The "first-time-borrower penalty" in E5 is **architectural and indistinguishable from a poverty penalty.**

### 5.3 The crossover regions

The four feature regimes that produce the largest cross-pipeline differences:

| Regime | E1 path | E5 path | Differential |
|---|---|---|---|
| CIBIL ∈ {0, −1} | re-routed to B | (B path runs) | high |
| CIBIL ∈ {100, 200, 300, 500, 540} | raises | n/a | system failure |
| CIBIL = 658 vs 659 | Unlikely | n/a | verdict flip |
| Same CIBIL, different house quality | n/a | 26-point score gap | housing proxy |

---

## 6. Failure Modes

### 6.1 F1. CRITICAL — First-time borrower is re-routed to a different model

**Evidence:** `routing.py:77` triggers when `cibil_val in (0, -1)`. A first-time borrower with no bureau score triggers the reroute. The rerouted payload is processed by E5 (readiness, rule-based, 0.6289 verdict potential). The thin-file 5-year borrower is processed by E1 (eligibility, ML, 0.6289 probability at CIBIL=700).

**Risk:** A first-time borrower receives a verdict from a rule-based system tuned to Person B. The verdict is not the verdict the system would produce if the borrower had a CIBIL. The first-time borrower is not treated as a thin-file person; they are treated as a different kind of person. The architecture has no concept of a "thin-file" borrower; it has a "reroute" trigger.

### 6.2 F2. CRITICAL — Model fails on 7 of 17 CIBIL values tested

**Evidence:** CIBIL ∈ {100, 200, 300, 500, 540, 900, 1000} all raise `CriticalEngineError`. Per [ML_AUDIT.md](ML_AUDIT.md) P3, no out-of-distribution detection exists. The system has no response other than a 500 error. The audit log receives no row for these failures (per the edge-case audit of Person B).

**Risk:** A borrower with a valid bureau score in the failure range cannot be assessed. The system returns an unhandled exception. The audit log is silent. The institution has no record that the assessment was attempted. The borrower is dropped.

### 6.3 F3. CRITICAL — Non-monotonic probability in the CIBIL sweep

**Evidence:** CIBIL=700 → prob 0.6289; CIBIL=800 → prob 0.5989. **A worse CIBIL gives a higher probability.** This is a model pathology, not a noise. Per [ML_AUDIT.md](ML_AUDIT.md) D1, the labels are rule-generated; the model has learned the rule with noise around the boundary.

**Risk:** A borrower who improves their CIBIL from 700 to 800 can be **rejected** by the system. The improvement is real (the bureau score increased), but the model's output moves in the wrong direction. **The system punishes improvement.**

### 6.4 F4. HIGH — E5's "5-year history" is a housing/infrastructure proxy, not a credit-history signal

**Evidence:** Person B's data has no `prior_loan` / `bureau` / `repayment_history` field. The "5-year history" persona is a synthetic construct using `type_of_house=T1` + `house_area=450` + `water=1.0` + `sanitary=1`. The 26-point score gap is driven entirely by housing and infrastructure.

**Risk:** Two distinct borrower profiles are indistinguishable to the system: (a) a first-time borrower who owns a pucca house with running water, and (b) a 5-year borrower who rents a kucha house without water. The system treats housing and infrastructure as a proxy for credit history, which is a **prohibited form of discrimination under ECOA** in the United States and **analogous provisions in Indian credit regulation**. Per `f6_feature_semantics.py:35-40`, the prior forensic already flagged `water_availability`, `sanitary_availability`, and `house_area` as **fair-lending proxies**.

### 6.5 F5. HIGH — Verdict-band boundary is a hard cliff

**Evidence:** CIBIL=658 → "Unlikely"; CIBIL=659 → "Likely." Per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §5, the underlying label rule has a discontinuity at CIBIL=549.5. The E1 verdict thresholds (0.80/0.60/0.40) are also hard boundaries.

**Risk:** A 1-point CIBIL change (658 → 659) flips the verdict from Unlikely to Likely. There is no human-readable explanation for the borrower. The system provides no recourse.

### 6.6 F6. MEDIUM — E1 top-3 driver includes "luxury_assets_value" with negative contribution for a 5y-history borrower with 0 luxury assets

**Evidence:** `feature_contributions` for `cibil_score=700, luxury_assets_value=0`: `luxury_assets_value` contributes −0.1353 to the probability. The applicant declared 0 luxury assets. The contribution is an artifact of `treeinterpreter` decomposing the model's bias, not a real economic signal.

**Risk:** A loan officer sees "luxury assets reduced your eligibility by 0.1353" for a borrower who declared 0 luxury assets. The rationale is fabricated. The officer cannot defend it. The borrower cannot dispute it.

### 6.7 F7. CRITICAL — No audit log row for failed first-time borrower assessments

**Evidence:** The edge-case audit of `execute_orchestrator` showed that exceptions (CIBIL=100, 200, 300, 500, 540, 900, 1000; loan_amount=-5000; income=-100) **do not write to `audit_log`**. A first-time borrower who triggers any of these failures has no record in the system.

**Risk:** The institution has no way to count, audit, or defend against first-time-borrower denials caused by system failure. The failure is invisible to compliance. Per [ML_AUDIT.md](ML_AUDIT.md) MC9, post-hoc fairness audits cannot be performed on the audit log.

---

## 7. Regulatory Risk

### 7.1 ECOA / Reg B (United States) — analogous Indian context

Per `f6_feature_semantics.py:14-40` (referenced in [DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md) §3.3), the prior forensic flagged:

- `dependents` — "Fair Lending / ECOA Proxy Risk (Familial Status)"
- `education` — "Fair Lending / Redlining Proxy Risk"

These proxies are consumed by E1. Per [ML_AUDIT.md](ML_AUDIT.md) F1, the dataset has no protected-class columns, but the **proxies** (dependents, education) are present. E1's 79.7% SHAP attribution to CIBIL **does not eliminate proxy risk** because the E1 model output is treated as a credit decisioning rationale.

### 7.2 RBI Fair Practices Code

Per the RBI's Master Direction on Fair Practices Code for lenders, credit decisions must be:

- Communicated in writing
- Accompanied by reasons for rejection upon request
- Subject to a grievance mechanism

The current system provides:

- A 5-line rationale embedded in `feature_contributions` (per the architecture)
- A "Floor breach" override flag with no borrower-readable explanation
- No mechanism for the borrower to dispute the bureau-based decision

### 7.3 Credit Information Companies (Regulation) Act, 2005 (CICRA)

Per `myFunction.py` and the Indian bank CSVs in `data/raw/`, the institution is processing **RBI-published wilful defaulter lists** without explicit CICRA compliance evidence. The prior audit flagged this as **legally uncertain** (see [DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md) §1.7). A first-time borrower in India is **most likely** a thin-file borrower; the system treats them as a different kind of person; this is the regulator's primary concern.

### 7.4 EU AI Act (analogous)

The system is a "high-risk AI" under EU AI Act classification (Annex III, §5(b) — creditworthiness assessment). Required controls:

- Training data governance (absent — see [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md))
- Record-keeping (partial — `audit_log` exists but exceptions don't write)
- Transparency (partial — verdict and override are exposed; rationale is in feature_contributions)
- Human oversight (partial — Approve/Decline/Escalate buttons exist, but Escalate is stubbed)
- Accuracy, robustness, cybersecurity (fails — model raises on 7 of 17 inputs, non-monotonic probability)

**A first-time borrower is precisely the population the EU AI Act's high-risk classification is meant to protect.** The system's treatment of this population is the most consequential regulatory exposure.

---

## 8. Recommended Remediations

### R1. Add a "thin file" path that does not re-route

`routing.py:77-80` should be replaced with:

- If `cibil_val` is missing/0/−1, **use CIBIL = NaN as a feature** and let E1 produce a verdict with a special "thin file" flag.
- Do not convert the applicant to the Person B schema. The conversion assumes Person A fields that the first-time borrower does not have.

### R2. Add OOD detection for the eligibility model

Per [ML_AUDIT.md](ML_AUDIT.md) Fix 6. For each input feature, compare the live value against the training distribution. If outside, return an `OUT_OF_DISTRIBUTION` error envelope with the specific feature. Do not raise. Do not silently impute 0.

### R3. Calibrate the model and remove hard verdict thresholds

Per [ML_AUDIT.md](ML_AUDIT.md) C1 and Fix 11. Apply `CalibratedClassifierCV` and re-derive the verdict thresholds from a cost-of-error analysis. A 1-point CIBIL change should not flip the verdict.

### R4. Add a real credit-history feature to E5

Person B's data has no prior-loan, bureau, or repayment-history column. If the institution serves thin-file borrowers, the schema should at minimum include:

- `prior_loans_count` (integer, 0..N)
- `repayment_history` (categorical: never, on-time, late, default)
- `time_since_first_credit` (integer months)

These are the actual signals the system needs. Without them, the system cannot assess credit history; it can only assess housing.

### R5. Write audit rows for failed assessments

Per [ML_AUDIT.md](ML_AUDIT.md) P1 and the edge-case audit. The orchestrator must catch `CriticalEngineError`, write a structured audit row with the failure category, and return a `500` with a recoverable error envelope. The current code path does not.

### R6. Remove the fabricated archetype label from the production response

Per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §7. The KMeans that produced the "Educated Professionals" cluster is broken. E3 should not be in the production response until a defensible clustering is in place.

### R7. Make the E1 `feature_contributions` defensible

Per [ML_AUDIT.md](ML_AUDIT.md) E1. A loan officer should not see "luxury_assets_value: −0.1353" for a borrower who declared 0 luxury assets. The contributions should be filtered, normalized, or suppressed for features whose value is at the floor or the ceiling.

### R8. Provide recourse for first-time borrowers

The system currently has no mechanism for a first-time borrower to provide supplementary evidence (e.g., utility bills, rent receipts, business income statements) that would substitute for a bureau score. The institution should add a "supplementary information" intake path that, when populated, provides the E1 model with non-bureau proxies for creditworthiness.

### R9. Document the system's treatment of first-time borrowers in plain language

The current `audit_log` records `OVERRIDE_E2_P4_REJECTION` and `REROUTE_NTC_TO_PERSON_B` but the borrower-facing and regulator-facing explanation is missing. A single document "How we assess thin-file borrowers" should be published.

### R10. Disable Person A path for first-time borrowers until the underlying model is calibrated

Until R2 and R3 are complete, the institution should:

- Detect CIBIL=0/−1 at the API edge.
- Return a `THIN_FILE_NOT_SUPPORTED` error envelope with a clear message and a manual-review link.
- Do not silently reroute.

The current rerouting is a **silent** treatment of a vulnerable population. That is the failure.

---

## 9. Final Verdict

| Dimension | Status |
|---|---|
| First-time borrower receives fair opportunity | **NO.** Re-routed to a different model based on a single feature. |
| E1 features that reward credit history | Only `cibil_score`. No `prior_loans`, no `repayment_history`, no `banking_relationship_duration`. |
| E2 features that reward credit history | Only `cibil_score`. |
| E5 features that reward credit history | **NONE.** E5 has no credit-history features. The "5y history" persona is a housing/infrastructure proxy. |
| E6 features that reward credit history | **NONE.** E6 has no credit-history features. |
| Absolute score difference (Person A no-history vs 5y history) | undefined → 0.6289. |
| Absolute score difference (Person B no-history vs 5y history) | 53 → 79 (+26). |
| Threshold crossings (Person A path) | 1 (CIBIL=658 → CIBIL=659, Unlikely → Likely). |
| Threshold crossings (Person B path) | 1 (Moderately Ready → Ready). |
| Final recommendation difference | **Different engine output for Person A no-history vs 5y history.** Person A no-history gets a Person B recommendation. Person A 5y-history gets a Person A recommendation. |
| Verdict | **FAIL.** |

**Risk rating:** **CRITICAL** for the first-time borrower segment.

**Specific regulatory exposure:**

- **ECOA / Fair Lending** — proxy risk via `dependents`, `education`, housing, infrastructure features. F4.
- **RBI Fair Practices Code** — no borrower-readable rationale, no grievance mechanism. F5.
- **CICRA** — wilful defaulter data processed without compliance evidence. Per [DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md) §1.7.
- **EU AI Act** — high-risk AI with no training data governance, no OOD detection, no accurate model. Per [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md).

**Specific operational failures:**

- F1: silent re-routing to wrong model
- F2: 7 of 17 CIBIL values raise unhandled exception
- F3: non-monotonic probability (CIBIL 700 → 800 reduces approval probability)
- F4: 5-year history is indistinguishable from "pucca house with water"
- F5: hard verdict cliffs at CIBIL=659 and probability=0.60
- F6: fabricated feature contributions
- F7: failed assessments leave no audit trail

**Binding remediation:** **Disable the Person A path for CIBIL=0/−1 until R1–R3 are complete.** A first-time borrower should receive an explicit "thin file" message, not a silent reroute, not a fabricated rationale, and not a missing audit row. The current behavior is the worst of all three.

---

## 10. Summary

| Item | Status |
|---|---|
| Total engines audited | 4 (E1, E2, E5, E6) |
| Engines with explicit credit-history features | 2 (E1, E2 — both via CIBIL only) |
| Engines with NO credit-history features | 2 (E5, E6) |
| Personas tested | 4 (A no-history, A 5y history, B no-history, B 5y history) |
| Threshold crossings | 2 |
| Model failures on valid inputs | 7 of 17 CIBIL values |
| Audit-log rows for failed assessments | **0** |
| Final verdict | **FAIL** |
| Risk rating | **CRITICAL** |
| Recommended action | **Disable Person A path for CIBIL=0/−1 until R1–R3 are complete.** |

The institution has a first-time-borrower fairness problem before it has an ML problem. A first-time borrower is silently re-routed, given a verdict from a system that has no record of their credit history, and disappears from the audit log. The system does not need better ML. It needs to recognize that the absence of history is itself a signal that demands explicit treatment.
