# RiskIntel — Project Decisions Log

This document records architectural and design decisions made during RiskIntel development. Each entry captures the context, options considered, decision made, and rationale.

---

## Decision 001 — Frontend Framework

**Date:** 2026-06-05
**Status:** Decided

**Context:**
RiskIntel requires a web frontend for form input, result display, and report downloads.

**Options Considered:**

| Option | Pros | Cons |
| :--- | :--- | :--- |
| Flask + Jinja2 | Simple, single codebase | Limited interactivity, tight coupling |
| Vite + React | Rich UI, component reuse, SPA | More complex, separate build |
| Streamlit | Fastest prototype | Poor customization, not production-grade |

**Decision:** Vite + React frontend with Flask/FastAPI backend.

**Rationale:** The project requires rich interactive forms, dynamic result rendering, and a professional UI. React provides component reuse across Person A and Person B workflows. SPA architecture enables better UX for multi-step workflows.

---

## Decision 002 — PDF Report Engine

**Date:** 2026-06-05
**Status:** Decided

**Context:**
Bank employees need downloadable PDF underwriting reports.

**Options Considered:**

| Option | Pros | Cons |
| :--- | :--- | :--- |
| ReportLab | Industry standard, precise layout control | Steeper learning curve |
| WeasyPrint | CSS-based styling, fast design | External dependency (wkhtmltopdf) |
| FPDF2 | Lightweight, simple | Limited table/layout capabilities |

**Decision:** ReportLab.

**Rationale:** ReportLab is the industry standard for programmatic financial PDF generation. It provides the pixel-perfect control needed for professional underwriting documents with tables, branding, and structured sections.

---

## Decision 003 — Database

**Date:** 2026-06-05
**Status:** Decided

**Context:**
The system needs to store past assessment results for report generation and audit trail.

**Options Considered:**

| Option | Pros | Cons |
| :--- | :--- | :--- |
| Stateless (no DB) | Simplest | No history, no report retrieval |
| SQLite | Lightweight, zero-config, file-based | Single-writer, not ideal for high concurrency |
| PostgreSQL | Production-grade, concurrent | Overkill for V1, requires setup |

**Decision:** SQLite with lightweight persistence.

**Rationale:** V1 is a portfolio/demo project. SQLite provides persistence for assessment history and report metadata without infrastructure overhead. Migration to PostgreSQL is straightforward if needed later.

---

## Decision 004 — Person B: No Approval Probability

**Date:** 2026-06-05
**Status:** Decided

**Context:**
Dataset B (RuralCreditData) contains no approval labels. Generating a synthetic approval probability would be misleading.

**Decision:** Person B outputs a Readiness Score (0–100) and Readiness Band. No approval probability is generated or displayed.

**Rationale:** Readiness ≠ Approval. Presenting a fake probability violates the project's transparency goal. The readiness score communicates preparedness honestly.

---

## Decision 005 — Risk Tier Interpretation

**Date:** 2026-06-05
**Status:** Decided

**Context:**
In Dataset C, `Approved_Flag` is highly correlated with Credit Score. Using it as a default-risk outcome would be misleading.

**Decision:** Risk Tier (P1–P4) is treated as a policy/risk-grade signal derived from credit profile features, not as a probability of default.

**Rationale:** The correlation between approval and credit score makes the label a poor proxy for actual default risk. Framing it as a risk grade (similar to bank internal ratings) is more honest and useful.

---

## Decision 006 — Model Serialization

**Date:** 2026-06-05
**Status:** Decided

**Decision:** Use `joblib` for model serialization.

**Rationale:** `joblib` is optimized for objects containing large numpy arrays (common in scikit-learn pipelines). It is faster and produces smaller files than `pickle` for ML models.

---

## Template for Future Decisions

```markdown
## Decision NNN — Title

**Date:** YYYY-MM-DD
**Status:** Proposed / Decided / Superseded

**Context:**
What is the issue?

**Options Considered:**
| Option | Pros | Cons |

**Decision:**
What was decided.

**Rationale:**
Why this option was chosen.
```
