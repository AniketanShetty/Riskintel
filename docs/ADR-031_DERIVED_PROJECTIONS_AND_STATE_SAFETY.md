# ADR-031: Derived Projections and State Safety

**Date:** 2026-06-14
**Status:** ACCEPTED
**Resolves:** Architecture Review Board conflict regarding `emi_shortfall`, `aa_retry_count`, and `fo_retry_count` physical persistence vs derivation.

---

## 1. Context

RiskIntel V2 Phase 1 established a strict PostgreSQL persistence layer (ADR-021, 023, 025). During the transition to Phase 2 Orchestration, a schema conflict arose regarding whether the system should physically store derived variables (e.g., `emi_shortfall = target_emi - available_capacity`) and mutable tracking counts (`aa_retry_count`) on parent records.

## 2. Decision

The Architecture Review Board strictly prohibits the persistence of mathematically redundant fields and detached mutable counters. 

**Rule 1: No Derived Math Persistence**
If a variable is mathematically derived from two or more immutable facts that are already persisted, the derived variable must **not** exist as a physical database column. It must be implemented as a dynamic Python `@property` to prevent any possibility of database normalization failure or "split-brain" drift.
*   **Outcome:** `emi_shortfall` is dropped from `optimization_results`.

**Rule 2: No Detached Event Counters**
Retry counts must be evaluated by querying the actual immutable audit ledger (`verification_records`). Updating a scalar integer `retry_count` on the `ApplicationSession` risks an irreversible drift if the corresponding physical `VerificationRecord` fails to insert correctly.
*   **Outcome:** `aa_retry_count` and `fo_retry_count` are dropped from `application_sessions`.

## 3. Consequences

*   **Positive:** The PostgreSQL database is perfectly normalized. State divergence between a count integer and the actual number of logged attempts is physically impossible. 
*   **Negative:** Raw SQL analytics queries cannot simply execute `WHERE emi_shortfall > X` natively; they must use explicit algebra `WHERE target_emi - available_capacity > X`.
*   **Implementation:** Migration `003_architecture_reconciliation` enforces these teardowns.
