# ARCHITECTURE_AUTHORITY_MATRIX.md

## Purpose
This document defines the authoritative artifact for every disputed architectural decision in RiskIntel V2.

**Rule:** If two artifacts disagree, the higher-authority artifact wins.

---

## Authority Order

1. Constitution
2. Accepted ADRs
3. Database Constraints / Migrations
4. PROJECT_STATE.md
5. Implementation Code
6. Tests
7. Planning Documents

---

## Topic: Optimization Verdicts

**Authority:** Database CheckConstraint
**Current Reality:** `READY`, `NEARLY_READY`, `NOT_READY_YET`
**Decision:** Implementation must conform. The math engine must never return `COAPPLICANT_REQUIRED` as a string status; it must use `NOT_READY_YET` and set the `coapplicant_required` boolean.
**Status:** LOCKED

---

## Topic: Retry Count Ownership

**Authority:** ADR-031
**Candidate Accepted:** Derived from `VerificationRecord` history
**Decision:** `aa_retry_count` and `fo_retry_count` physical columns are anti-patterns that create split-brain state risks. They are dropped via Alembic Migration 003 and replaced with functional Python `@property` evaluators on `ApplicationSession`.
**Status:** RESOLVED

---

## Topic: EMI Persistence

**Authority:** ADR-027
**Required Fields:** `target_emi`, `contract_emi`
**Decision:** Both `target_emi` (requested burden) and `contract_emi` (approved burden) must be stored physically to prevent downstream floating-point drift. Both are strictly bounded to `ROUND_CEILING` algebra.
**Status:** RESOLVED

---

## Topic: emi_shortfall

**Authority:** ADR-031
**Decision:** `emi_shortfall` is a pure mathematical derivation (`target_emi - available_capacity`). Storing it physically violates event sourcing principles. It is dropped via Alembic Migration 003 and replaced with a Python `@property`.
**Status:** RESOLVED
