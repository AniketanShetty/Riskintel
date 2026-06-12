# RiskIntel Project State

**Last updated:** 2026-06-10 · **Phase:** V2 Guardrails Implementation · **Tests:** 323 / 323 pass · **Freeze status:** FROZEN FOR FIRST SUBMISSION (post-frontend-constitution)

---

## 1. Constitution (read first, before any change)

1. **Repository Reality > Documentation.** If code, a test, or a live request contradicts this file, the file is wrong. Verify with a command or a test before editing the file.
2. **UNKNOWN > Guessing.** If a value is not in the repository (constant, JSON, or test), mark it UNKNOWN. Do not invent thresholds, timelines, ratios, or rules of thumb.
3. **PROJECT_STATE.md is the canonical memory layer.** Chat history and governance docs are scratch. This file is truth.
4. **No silent scope changes.** A change that touches a new file, a new engine, or a new rule is a scope change. Document it in the Change Log before or immediately after the edit. Do not let scope drift.
5. **Update PROJECT_STATE.md after every meaningful architectural change.** A change to a rule's `condition_callable`, a new endpoint, a schema addition, or a new SSOT block is meaningful. A typo fix is not. Use judgment.
6. **No frontend work in this file's normal updates.** The frontend has its own audit and contract (see §5).

## 2. System Overview

### Mission
Explainable AI underwriting for microfinance. Two pipelines (Person A — credit-eligibility; Person B — new-to-credit / livelihood) emit a structured `DecisionExplanation` that a loan officer can defend in 30 seconds.

### Person definitions
- **Person A** — borrower with a CIBIL score. Pipeline: E1 (eligibility) → E2 (risk tier) → E3 (archetype) → E4 (recommendation).
- **Person B** — NTC / no-CIBIL borrower. Pipeline: E5 (readiness) → E6 (livelihood) → E4 (recommendation). Also reached via NTC reroute from Person A when `cibil_score in {0, -1}`.

### Engine registry
| ID | File | Purpose | Critical? | Override behavior |
|---|---|---|---|---|
| E1 | `backend/app/engines/eligibility/eligibility_engine.py` | Eligibility ML (probability + SHAP-style contributions) | **Yes** — HTTP 500 on failure | Drift tolerance: probability decomposition drift > 1e-3 → `engine_statuses["E1"]="drift_degraded"`, no 500 |
| E2 | `backend/app/engines/risk_tier/risk_tier_engine.py` | CIBIL → P1/P2/P3/P4 tier (JSON SSOT) | **Yes** — HTTP 500 on failure | n/a |
| E3 | `backend/app/engines/borrower_archetype/` | Demographic archetype cluster | No — degraded fallback `{label: "Unclassified", cluster_id: -1}` | n/a |
| E4 | `backend/app/engines/recommendation/` | Recommendation engine (12 rules, threshold-gated, governance-fail-loud) | No — degraded fallback `{primary_reason: "completed under degraded mode.", contributing_factors: []}` | n/a |
| E5 | `backend/app/engines/readiness/readiness_engine.py` | 5-component readiness score + band, plus FH-floor override | **Yes** — HTTP 500 on failure | FH < 0.5 → forced `Not Ready`, score=0 |
| E6 | `backend/app/engines/livelihood/` | Business macro + loan-purpose alignment | No — degraded fallback `{label: "General Micro-Enterprise", cluster_id: 0}` | n/a |

### Tech stack
- **Backend**: FastAPI + SQLite (authoritative persistence) + Pydantic schemas + SQLAlchemy.
- **ML**: scikit-learn (E1 DecisionTreeClassifier) + custom thresholds (E2, E5).
- **Audit**: SQLite `audit_log` table, fail-closed on write.
- **Frontend**: Vite + React 19 SPA (currently Vite scaffold; RiskIntel pages TBD).

### Entry points
- `backend/run.py` — `uvicorn.run("app.main:app", ...)` (rewritten 2026-06-07; not the Flask factory).
- FastAPI routers in `backend/app/api/assess.py`:
  - `POST /api/assess` — unified gateway (routing inferred from payload).
  - `POST /api/assess/person-a` — forces Person A path. **Note**: F6 fix removed the hardcoded `response_model=PersonAResponse` so NTC reroute can serve the Person B response on this endpoint.
  - `POST /api/assess/person-b` — forces Person B path. Same response_model fix.
- Health: `/health/live`, `/health/ready`, `/health/deep` (all 200 when backend is up).

### Test commands
```bash
cd backend
./venv/Scripts/python.exe -m pytest tests/ -q          # 323 / 323 expected
```

### Run commands
```bash
cd backend
./venv/Scripts/python.exe run.py                     # boots uvicorn on 0.0.0.0:8000
# In another terminal:
curl -s http://localhost:8000/health/ready | python -m json.tool
open http://localhost:8000/docs                          # OpenAPI / Swagger UI
```

---

## 3. SSOT Registry (canonical sources — read these before guessing values)

| Concern | Source | Path |
|---|---|---|
| CIBIL → risk tier cutoffs (P1/P2/P3/P4) | JSON SSOT | `data/processed/risk_tier_thresholds.json` |
| Readiness thresholds (Strong/Satisfactory, band cutoffs, FH floor) | Module constants | `backend/app/engines/readiness/readiness_engine.py` (class `ReadinessEngine`: `STRONG_STATUS_MIN=70`, `SATISFACTORY_STATUS_MIN=50`, `BAND_READY_MIN=75`, `BAND_MODERATELY_READY_MIN=50`, `BAND_NEEDS_IMPROVEMENT_MIN=25`, `FINANCIAL_HEALTH_FLOOR_THRESHOLD=0.5`) |
| Translation map (raw keys → plain language) | Module | `backend/app/engines/recommendation/translations.py` (`FEATURE_TRANSLATIONS`, `TIER_TRANSLATIONS`) |
| Recommendation governance thresholds | `ctx['risk_tier']['threshold_values']` (E2) and `ctx['readiness']['thresholds']` (E5) — engine-surfaced SSOT blocks | The recommendation engine reads these via `_required_threshold(ctx, dotted_path)` which raises `GovernanceError` on missing values |
| Routing logic (NTC reroute) | Module | `backend/app/routing.py` |
| Lifecycle constants | Module | `backend/app/orchestrator.py` (`API_VERSION`, `REQUEST_SCHEMA_VERSION`, `DECISION_VERSION`, `RECOMMENDATION_VERSION`) |
| Recommendation engine version | Module | `backend/app/engines/recommendation/recommendation_engine.py` (`RECOMMENDATION_VERSION = "1.2"`) |
| Audit schema (13 columns) | Migration | `backend/app/audit.py` |

**To find a value**: search the SSOT Registry above first. If not listed, search the file:line in the Source Code Pointer column. If still not found, the value is UNKNOWN.

---

## 4. Current Project State

| Field | Value |
|---|---|
| **Date** | 2026-06-10 |
| **Phase** | V2 Guardrails Implementation (Person A & B Guardrails Complete) |
| **Freeze status** | FROZEN FOR FIRST SUBMISSION (Frontend Constitution adopted 2026-06-07; see §7) |
| **Current blockers** | None |
| **Current risks** | (1) A-RISK-001 verdict-polarity gap. (2) 1-point CIBIL cliff at 658→659. (3) `infrastructure_access` and `household_burden` silent components. (4) E1 dataset failed forensic audit. (5) `Loan_Default1.csv` failed Domain Alignment Audit. |
| **Next action** | Execute Option B Architecture: Demote the E1 ML pipeline and build a deterministic Unified Scorecard (Person A + Person B). Implement the Optimization Engine with Utility-Aware logic and the 'Pending Verification' freeze protocol for unverified cash borrowers. |
| **Test status** | 323 / 323 pass. |

---

## 5. Frontend Contract (Borrower / Mentor API consumer)

### Borrower-visible fields
- `status`, `user_type`, `correlation_id` (envelope).
- `routing_decision.{original_user_type, routed_to, reason}` — when NTC reroute fires.
- `eligibility.{verdict, probability, bias, feature_contributions, policy_override_applied}` (Person A).
- `risk_tier.{tier, label, description, score_used, thresholds, threshold_values}` (Person A).
- `archetype.{label, description, cluster_id, is_unclassified}` (both).
- `readiness.{score, band, components, metadata}` (Person B). `metadata.e5_thresholds` surfaces engine SSOT.
- `explanation.{decision_verdict, primary_reason, contributing_factors[]}` where each factor has `feature, value, evidence, reason, improvement_advice, advice_type, evidence_sources`.

### Mentor-visible fields (all borrower fields +)
- `risk_tier.threshold_values` (P1/P2/P3/P4 numeric cutoffs) — explicit so a mentor can defend the boundary.
- `readiness.metadata.e5_thresholds` (Strong/Satisfactory/band/FH-floor) — same.
- `eligibility.feature_contributions` (per-feature signed contribution) — shows which features drove the verdict.
- `explanation.contributing_factors[].evidence_sources` (JSON paths to engine inputs) — for deep audit.

### Hidden fields
- `applicant` (full echo of input payload, including protected-class fields). Display only; do not derive logic.
- `audit.policy_override_flags`, `audit.engine_statuses` — only in audit log, not in API response. Cross-reference via `correlation_id` for forensic review.

### Known frontend constraints
- `value: "Unknown"` is shown for Person B factors because the evaluator does `inputs.{feature_name}` and these features are not in `inputs`. **Frontend should substitute the score from `factor.evidence` or `readiness.components.{feature}.score`**.
- `archetype.label` is a free-form string; engine may add labels in V2. Frontend must not hard-code UI for specific labels.
- `routing_decision.reason` is undocumented codes (`cibil_absent_or_sentinel`, `user_type_person_b_or_cibil_absent`, `standard_person_a_pipeline`). Display as text; do not branch UI.
- B-side factors may fire with `purpose_alignment: "Misaligned"` even when `business_viability >= 70` — but B-IMP-002 is gated by `is_component_below_strong_threshold`, so the rule does NOT fire. **Frontend may want to surface the misalignment signal anyway (V2 candidate).**
- The `value: "Unknown"` display bug also affects the `feature_name` for B-side factors — frontend must not display the raw key.

### Policy override handling
- **P4 override**: detected by `verdict == "Unlikely" AND tier == "P4"` on a Person A response where E1 would have predicted a positive verdict. Surfaced to the borrower by **A-POLICY-001** (priority 95) which fires with reason: "Your application has strengths, but our policy requires a stronger credit tier than what your current credit profile demonstrates."
- **E5 floor breach**: detected by `readiness.band == "Not Ready" AND readiness.score == 0` regardless of the weighted sum. The audit log carries `policy_override_applied: true` on the engine response.
- **ML invariant drift (E1)**: detected by `engine_statuses["E1"] == "drift_degraded"` in the audit log. **Not surfaced on the API response** in V1.

### PDF strategy
- V1 demo: `window.print()` + `@media print` CSS. No runtime dependency. The "Why this decision?" panel prints to PDF via the browser's native dialog.
- V2: `@react-pdf/renderer` for a polished mentor packet.

---

## 6. Change Log (condensed historical milestones)

> Format: `[date] title. 1-line summary.`

**Phase 0 — bootstrapping (2026-06-07)**
- Init. `PROJECT_STATE.md` initialized after Repository Reality Audit.
- Run.py rewrite. `backend/run.py` (Flask → uvicorn) fixed startup; all `/health/*` and `/docs` return 200.
- V1 logic surfacing. `routing_decision`, `archetype.is_unclassified`, `readiness.metadata` exposed on API; audit schema migrated with 3 additive columns; 315 tests pass.
- Test contract alignment. 5 failing tests fixed (phantom `explanation` subkey, wrong `isinstance(list)`, malformed E4 mock). 317 → 315.

**Phase 1 — recommendation governance (2026-06-07)**
- DecisionExplanation audit (no code). Identified 5 gaps in `DecisionExplanation`: missing personalization, missing `decision_version`/`recommendation_version`, etc. Smallest fix proposed.
- Recommendation provenance. Additive `advice_type` (Literal["evidence_based","inferred","generic"]) and `evidence_sources` (List[str]) on `ExplanationFactor`, `ExplanationRule`, all 13 rules. 315 pass.
- Top-5 rule personalization. A-RISK-001, A-RISK-002, B-IMP-001, B-IMP-002, A-STR-003 interpolate applicant values + policy-backed thresholds. 315 pass.
- Human-language translation layer. `translations.py` added (28 raw keys → plain language, 14 jargon phrases). Money formatted ₹/lakh/crore. 315 pass.
- A-STR-003 safety hardening. `ACTIONABLE_FEATURES` whitelist; A-STR-003 split into actionable path + FALLBACK path (mentor escalation). 315 pass.
- B-IMP-002 evidence alignment. Rewrote advice/reason to reference only engine-evaluated factors (no invented documentation/registration language). 315 pass.

**Phase 2 — SSOT refactor + governance hardening (2026-06-07)**
- V1 Threshold Governance Refactor. Engine surfaces `thresholds` blocks; orchestrator derives display strings from engine values; rules read `p1_min`/`strong_min` via governance-fail-loud `_required_threshold` helper. New `GovernanceError` exception. 315 pass.
- V1 Threshold Governance Hardening. `evidence_sources` paths corrected to match API-visible paths; silent fallbacks removed; `GovernanceError` re-raise in evaluator. 315 pass.
- V1 Policy Override Governance Audit (no code). Inventoried 17 override sites; classified ownership; recommended **DOCUMENT** (not refactor). 7 audit-metadata fields flagged as NICE_TO_HAVE / V2.
- V1 Closure Audit. Reclassified 5 schema extensions as V2 / NICE_TO_HAVE. Recommended action: **CLOSE V1**. Stale entries cleaned.

**Phase 3 — freeze-blocker remediation (2026-06-07)**
- V1 Freeze-Blocker Remediation (F1..F6). 7 blockers fixed: A-FALLBACK-001 verdict-gate (F1), B-FALLBACK-001 band-gate (F1-B), B-STR-002 absolute threshold (F2), B-IMP-002 alignment guard (F3), B-STR-002 text truth (F4), E1 invariant degraded mode (F5), typed-endpoint NTC fix (F6). 315 pass.
- V1 Final Explainability Patch. A-POLICY-001 (P4 override explainer, priority 95) + B-IMP-002 anti-gaming wording. 315 pass.
- A-POLICY-001 advice revision. Removed two ungrounded values ("6-12 months" timeline, "credit-card balances well below their limits" rule-of-thumb) per Evidence-Grounded Actionability Audit. Replaced with advice referencing only the P3 threshold (credit score above 658). 315 pass.
- Readiness Recommendation Consistency Fix. Replaced bottom-2 ranking heuristic `has_low_component` with new `is_component_below_strong_threshold(ctx, component_name)` helper on B-STR-003, B-IMP-001, B-IMP-002. A component classified as "Strong" by E5 (score >= 70) can no longer trigger an improvement rule. Verified live: fh=70 → B-IMP-001 does NOT fire; fh=69 → B-IMP-001 fires. 315 pass.

**V1 certification: FREEZE READY** (2026-06-07).

**Phase 4 — frontend constitution adoption (2026-06-07)**
- Frontend Constitution (§7). Adopted borrower coaching principles, mentor X-ray mode, scope guardrails, 5 demo personas, frozen-for-first-submission status. No backend changes; no governance rules removed; no historical sections deleted.
- Mobile visual QA pass. Resolved 4 defects: AppHeader horizontal overflow at <=390px, brand subtitle overflow, OutcomeHero icon stacking on mobile, EvidenceDrawer button overflow. Touch targets preserved; desktop appearance unchanged; print output unchanged. 3 files modified, 14 lines net.

**Phase 5 — Verified P0 fixes (2026-06-07)**
- Relaxed `loan_amount` validation in `PersonARequest` (ge=100 → ge=1) to allow realistic NTC micro-loans.
- Explicitly documented `eligibility.policy_override_applied` in Person A responses contract.

---

## 7. Frontend Constitution (V1 — 2026-06-07)

### Mission

RiskIntel is a borrower coaching experience, not an analytics dashboard.

### Borrower Principles

* Show outcome first.
* Show strengths before weaknesses.
* Show one primary action plan.
* Hide raw ML probabilities.
* Hide correlation IDs.
* Hide audit hashes.
* Hide policy metadata.
* Never use rejection-style language.

### Mentor Principles

* Mentor Mode must visibly change UI state.
* Mentor Mode reveals evidence, thresholds, routing decisions, and override information.
* Mentor Mode must feel distinct from borrower mode.
* Evidence must always be traceable to backend fields.

### Scope Guardrails

Build:

* Persona Selector
* Borrower View
* Mentor Mode
* Override Banner
* Evidence Drawer
* PDF Export

Do Not Build:

* Authentication
* Admin Dashboard
* Policy Editor
* Analytics
* Multi-user workflows
* Notifications
* Database management screens

### Demo Personas

1. Person A Approval
2. Person A Policy Override
3. Person B Ready
4. Person B Business Misalignment
5. Person B Financial Health Coaching

### Backend Freeze Status

Status: FROZEN FOR FIRST SUBMISSION

Known Deferred Issues:

* Eligibility monotonicity review (V2)
* Payload hash audit improvements (V2)
* Validation UX improvements (V2)

Frontend Blockers:

* None

### Frontend Success Criteria

A mentor should be able to:

1. Load a persona.
2. Understand the decision in under 10 seconds.
3. Explain the decision.
4. Reveal the evidence.
5. Export a report.

---

## Settled Decisions
1. `PROJECT_STATE.md` is the canonical memory layer. Maintained as truth.
2. Repository reality supersedes documentation.
3. Backend = FastAPI + SQLite. Authoritative persistence layer = SQLite.
4. Recommendation governance discipline: every threshold reads from engine SSOT, raises `GovernanceError` on missing, never silently substitutes a hardcoded value.
5. A-STR-003 actionability filter: improvement advice only fires on actionable features (`loan_amount`, `loan_term`, `cibil_score`). Non-actionable features (e.g. `annual_income`) get a mentor-escalation fallback.
6. P4 override is a policy decision, not a model decision. A-POLICY-001 is the dedicated explainer.

## Open Questions
- **run.py convention** (V2 candidate): remove in favor of Makefile / `uvicorn` CLI, or keep as the canonical entry point?
## AI OPERATING RULES

1. Read PROJECT_STATE first.
2. Read DECISIONS second.
3. Read BACKLOG third.
4. Ignore archive unless explicitly asked.
5. Repository reality overrides docs.
6. Unknown = UNKNOWN.
7. Never assume.
8. Update PROJECT_STATE after major changes.
9. Update DECISIONS after architectural changes.
10. Update BACKLOG after sprint completion.