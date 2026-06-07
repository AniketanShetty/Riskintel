-- ==============================================================================
-- RiskIntel V1 Schema Initialization
-- Purpose: Create the core tables for the RiskIntel assessment platform
-- Compliance: Enforces FCRA/ECOA traceability and immutable audit logging
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. APPLICANTS
-- Stores PII and core identity vectors. Tax IDs are hashed for security.
CREATE TABLE applicants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    tax_id_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_applicants_email ON applicants(email);
CREATE INDEX idx_applicants_tax_id_hash ON applicants(tax_id_hash);


-- 2. ASSESSMENTS
-- Tracks the lifecycle of a specific application execution DAG.
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    applicant_id UUID NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    input_features JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_status CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'FAILED_PROCESSING'))
);

CREATE INDEX idx_assessments_applicant_id ON assessments(applicant_id);
-- GIN index allows fast querying inside the JSONB payload
CREATE INDEX idx_assessments_features_gin ON assessments USING GIN (input_features);


-- 3. RULE_REGISTRY
-- Tracks versioned configurations for deterministic engines (E1, E2, E5).
CREATE TABLE rule_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engine_id VARCHAR(50) NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    logic_payload JSONB NOT NULL,
    version VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(engine_id, version)
);

-- Partial index for fast lookups of active rules
CREATE INDEX idx_active_rules ON rule_registry(engine_id) WHERE is_active = TRUE;


-- 4. MODEL_REGISTRY
-- Tracks versioned machine learning artifacts for predictive engines (E3, E4).
CREATE TABLE model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engine_id VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    artifact_s3_uri VARCHAR(512) NOT NULL,
    training_data_hash VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(engine_id, model_version)
);

-- Partial index for fast lookups of active models
CREATE INDEX idx_active_models ON model_registry(engine_id) WHERE is_active = TRUE;


-- 5. ARCHETYPE_RESULTS (E3)
-- Stores ML clustering outputs. Strictly linked to the exact model version used.
CREATE TABLE archetype_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES model_registry(id),
    archetype_label VARCHAR(100) NOT NULL,
    cluster_distances JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id)
);

CREATE INDEX idx_archetype_assessment ON archetype_results(assessment_id);


-- 6. RECOMMENDATION_RESULTS (E4)
-- Stores predictive limit recommendations. Linked to the exact model version used.
CREATE TABLE recommendation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES model_registry(id),
    suggested_limit NUMERIC(15, 2) NOT NULL,
    improvement_actions JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id)
);

CREATE INDEX idx_recommendation_assessment ON recommendation_results(assessment_id);


-- 7. AUDIT_LOG
-- Immutable ledger tracking Orchestrator DAG state transitions.
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    correlation_id UUID NOT NULL,
    engine_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_assessment_id ON audit_log(assessment_id);
CREATE INDEX idx_audit_correlation_id ON audit_log(correlation_id);
-- Temporal indexing for rapid time-series compliance searches
CREATE INDEX idx_audit_logged_at ON audit_log(logged_at);

-- Trigger to prevent updates to the audit_log table
CREATE OR REPLACE FUNCTION prevent_audit_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Updates to the audit_log table are strictly prohibited for compliance reasons.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_audit_update
BEFORE UPDATE ON audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_audit_update();
