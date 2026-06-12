"""v2_init: Phase 1 schema

Revision ID: 001_v2_init
Revises: 
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa

revision = "001_v2_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. application_sessions
    op.create_table(
        "application_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("current_state", sa.String(30), nullable=False, server_default="INTAKE"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("loan_amount", sa.Integer, nullable=False),
        sa.Column("loan_term", sa.Integer, nullable=False),
        sa.Column("loan_purpose", sa.String(30), nullable=False),
        sa.Column("income_bracket", sa.String(15), nullable=False),
        sa.Column("bureau_gate_status", sa.String(15), nullable=True),
        sa.Column("triage_pass", sa.Boolean, nullable=True),
        sa.CheckConstraint("loan_amount >= 1000 AND loan_amount <= 500000", name="chk_loan_amount_bounds"),
        sa.CheckConstraint("loan_term IN (12, 18, 24, 36, 48, 60)", name="chk_loan_term_valid"),
        sa.CheckConstraint("current_state IN ('INTAKE', 'TRIAGE', 'PENDING_VERIFICATION', 'PENDING_REPROMPT', 'VERIFIED', 'OPTIMIZATION', 'READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_application_state_enum"),
        sa.CheckConstraint("loan_purpose IN ('medical', 'working_capital', 'education', 'home_repair', 'debt_consolidation', 'wedding', 'two_wheeler')", name="chk_loan_purpose_enum"),
        sa.CheckConstraint("income_bracket IN ('0-10k', '10k-20k', '20k-30k', '30k-40k', '40k-50k', '50k+')", name="chk_income_bracket_enum"),
        sa.CheckConstraint("bureau_gate_status IS NULL OR bureau_gate_status IN ('PRIME', 'SUB_PRIME', 'THIN_FILE')", name="chk_bureau_gate_status_enum")
    )

    # 2. applicant_profiles
    op.create_table(
        "applicant_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False),
        sa.Column("is_co_applicant", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("national_id", sa.String(12), nullable=False),
        sa.Column("pincode", sa.String(6), nullable=False),
        sa.Column("canonical_verified_income", sa.Integer, nullable=True),
        sa.Column("canonical_vintage_months", sa.Integer, nullable=True),
        sa.Column("canonical_verification_pass", sa.Boolean, nullable=True),
        sa.Column("co_app_canonical_verification_pass", sa.Boolean, nullable=True),
        sa.Column("co_app_pathway", sa.String(10), nullable=True),
        sa.Column("cibil_score", sa.Integer, nullable=True),
        sa.Column("national_id_match_score", sa.Float, nullable=True),
        sa.CheckConstraint(
            "is_co_applicant = TRUE OR (full_name IS NOT NULL AND national_id IS NOT NULL AND pincode IS NOT NULL)",
            name="chk_primary_applicant_required_fields"
        ),
        sa.UniqueConstraint("session_id", "is_co_applicant", name="uq_session_applicant_type"),
    )

    # 3. verification_records
    op.create_table(
        "verification_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("received_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("verification_source", sa.String(25), nullable=False),
        sa.Column("verification_status", sa.String(30), nullable=False),
        sa.Column("verified_monthly_cash_income", sa.Integer, nullable=True),
        sa.Column("secondary_contact_number", sa.String(15), nullable=True),
        sa.Column("fo_visit_photo_hash", sa.String(64), nullable=True),
        sa.Column("tamper_evidence_pass", sa.Boolean, nullable=True),
        sa.Column("artifact_type", sa.String(25), nullable=True),
        sa.Column("artifact_issue_date", sa.Date, nullable=True),
        sa.Column("artifact_hash", sa.String(64), nullable=True),
        sa.Column("business_vintage_months_derived", sa.Integer, nullable=True),
        sa.CheckConstraint(
            "business_vintage_months_derived IS NULL OR business_vintage_months_derived >= 0",
            name="chk_vintage_months_nonnegative"
        ),
        sa.CheckConstraint(
            "verified_monthly_cash_income IS NULL OR verified_monthly_cash_income >= 0",
            name="chk_verified_income_nonnegative"
        ),
        sa.CheckConstraint("verification_source IN ('FIELD_OFFICER', 'ACCOUNT_AGGREGATOR')", name="chk_verification_source_enum"),
        sa.CheckConstraint("verification_status IN ('VERIFIED_CLEAN', 'VERIFIED_WITH_VARIANCE', 'FRAUD_DETECTED', 'UNREACHABLE', 'MISSING_SECONDARY_CONTACT')", name="chk_verification_status_enum"),
        sa.CheckConstraint("artifact_type IS NULL OR artifact_type IN ('municipal_license', 'rent_agreement', 'merchant_qr', 'none')", name="chk_artifact_type_enum"),
        sa.UniqueConstraint("session_id", "attempt_number", name="uq_verification_attempt"),
    )

    # 4. optimization_results
    op.create_table(
        "optimization_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False, unique=True),
        sa.Column("computed_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("repayment_trust", sa.String(4), nullable=False),
        sa.Column("available_capacity", sa.Integer, nullable=False),
        sa.Column("emi_shortfall", sa.Integer, nullable=False),
        sa.Column("approved_loan_amount", sa.Integer, nullable=False),
        sa.Column("approved_tenure", sa.Integer, nullable=False),
        sa.Column("coapplicant_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("required_coapplicant_income_baseline", sa.Integer, nullable=True),
        sa.Column("decision_verdict", sa.String(20), nullable=False),
        sa.Column("primary_reason", sa.String(500), nullable=False),
        sa.Column("recovery_roadmap", sa.String(2000), nullable=True),
        sa.Column("livelihood_resilience_pass", sa.Boolean, nullable=False, server_default="false"),
        sa.CheckConstraint(
            "approved_loan_amount >= 1000 AND approved_loan_amount <= 500000",
            name="chk_approved_amount_bounds"
        ),
        sa.CheckConstraint(
            "approved_tenure >= 12 AND approved_tenure <= 60",
            name="chk_approved_tenure_bounds"
        ),
        sa.CheckConstraint("repayment_trust IN ('PASS', 'FAIL')", name="chk_repayment_trust_enum"),
        sa.CheckConstraint("decision_verdict IN ('READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_decision_verdict_enum")
    )

    # 5. state_transition_events
    op.create_table(
        "state_transition_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("application_sessions.id"), nullable=False),
        sa.Column("from_state", sa.String(30), nullable=False),
        sa.Column("to_state", sa.String(30), nullable=False),
        sa.Column("trigger_event", sa.String(100), nullable=False),
        sa.Column("occurred_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.CheckConstraint("from_state IN ('INTAKE', 'TRIAGE', 'PENDING_VERIFICATION', 'PENDING_REPROMPT', 'VERIFIED', 'OPTIMIZATION', 'READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_from_state_enum"),
        sa.CheckConstraint("to_state IN ('INTAKE', 'TRIAGE', 'PENDING_VERIFICATION', 'PENDING_REPROMPT', 'VERIFIED', 'OPTIMIZATION', 'READY', 'NEARLY_READY', 'NOT_READY_YET')", name="chk_to_state_enum")
    )

    # Indexes
    op.create_index("ix_sessions_state", "application_sessions", ["current_state"])
    op.create_index("ix_applicants_session", "applicant_profiles", ["session_id"])
    op.create_index("ix_verifications_session", "verification_records", ["session_id"])
    op.create_index("ix_events_session_time", "state_transition_events", ["session_id", "occurred_at"])

    # Audit Ledger Append-Only Trigger
    op.execute("""
    CREATE OR REPLACE FUNCTION block_update_delete()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'Updates and Deletes are strictly forbidden on the state_transition_events ledger.';
    END;
    $$ LANGUAGE plpgsql;
    """)
    op.execute("""
    CREATE TRIGGER trg_block_update_delete
    BEFORE UPDATE OR DELETE ON state_transition_events
    FOR EACH ROW EXECUTE FUNCTION block_update_delete();
    """)
    
    # application_sessions updated_at auto-trigger
    op.execute("""
    CREATE OR REPLACE FUNCTION set_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    op.execute("""
    CREATE TRIGGER trg_set_updated_at
    BEFORE UPDATE ON application_sessions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

def downgrade() -> None:
    # Drop Triggers and Functions
    op.execute("DROP TRIGGER IF EXISTS trg_set_updated_at ON application_sessions")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
    op.execute("DROP TRIGGER IF EXISTS trg_block_update_delete ON state_transition_events")
    op.execute("DROP FUNCTION IF EXISTS block_update_delete")

    # Drop Tables
    op.drop_table("state_transition_events")
    op.drop_table("optimization_results")
    op.drop_table("verification_records")
    op.drop_table("applicant_profiles")
    op.drop_table("application_sessions")
