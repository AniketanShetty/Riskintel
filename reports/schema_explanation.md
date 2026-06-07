# RiskIntel PostgreSQL Schema Explanation

**Role:** Principal Backend Architect  
**Status:** Implementation Specification  

## Overview
The `001_initial_schema.sql` migration file initializes the core relational database structures for the RiskIntel platform. This document explains the strategic engineering and compliance decisions embedded within the schema.

## Core Architectural Decisions

### 1. FCRA / ECOA Compliance by Design
To satisfy the Fair Credit Reporting Act (FCRA) and the Equal Credit Opportunity Act (ECOA), the schema enforces absolute traceability. 
*   **Immutable Initial State:** The `assessments` table stores the `input_features` as a `JSONB` payload. This captures the exact financial feature vector the millisecond the application was filed. If a user later updates their profile, this historical record remains untouched, ensuring we can defend exactly why a decision was made.
*   **Foreign Key Lineage:** The `archetype_results` table does not just store the string "Young Starters". It enforces a strict foreign key (`model_id`) back to the `model_registry`. This allows compliance officers to trace a specific prediction back to the exact version of the model, the S3 artifact URI, and the cryptographic hash of the training data used to generate that boundary.

### 2. The Immutable Ledger (`audit_log`)
The `audit_log` table acts as the asynchronous, append-only ledger for the Orchestrator DAG. 
*   **Trigger Protection:** A PL/pgSQL trigger (`trg_prevent_audit_update`) is actively deployed on this table. It will forcefully throw an exception if any service (or even a database administrator) attempts to run an `UPDATE` statement. This cryptographically guarantees the append-only nature of the ledger.
*   **Temporal Indexing:** The `idx_audit_logged_at` index ensures that time-series queries (e.g., pulling all audit trails for a specific week during a regulatory inquiry) execute rapidly without sequential table scans.

### 3. PII Hashing (`applicants` table)
Identity resolution is handled securely. The `tax_id_hash` column stores a salted SHA-256 hash of an applicant's SSN or PAN.
*   **Security Benefit:** If the database is compromised, plaintext SSNs are not exposed.
*   **Business Benefit:** The system can still enforce uniqueness and deduplication logic (e.g., preventing the same applicant from applying twice in 30 days) by querying against the hash index (`idx_applicants_tax_id_hash`).

### 4. Normalized ML / Rules Decoupling
The schema isolates outputs. Rather than a massive, wide `assessments` table with 50 nullable columns, we employ a normalized design.
*   `rule_registry` handles deterministic configuration for E1, E2, E5.
*   `model_registry` handles mathematical artifact references for E3, E4.
*   The output tables (`archetype_results`, `recommendation_results`) are separate entities linked 1:1 with the assessment. This allows the backend orchestrator to fail fast (e.g., rejecting an applicant at E1) without leaving empty, null-filled rows in the ML tables, heavily optimizing disk storage and database page caching.

### 5. Performance Indexing
*   **Partial Indexes:** The registries utilize `WHERE is_active = TRUE` partial indexes. The Rules Engine and ML Inference services will poll these tables frequently on startup. A partial index ensures that these queries scan an infinitesimally small B-Tree rather than the entire historical registry of deprecated models.
*   **JSONB GIN Indexes:** The `assessments` table uses a Generalized Inverted Index (GIN) on the `input_features` JSON payload. This allows data science teams to run complex analytical queries directly against the JSON structure (e.g., `WHERE input_features->>'cibil_score' > 700`) without massive performance penalties.
