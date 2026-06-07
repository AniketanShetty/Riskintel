"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-06-05 23:23:07.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # 1. Applicants Table
    op.create_table('applicants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('tax_id_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_applicants_email', 'applicants', ['email'], unique=False)
    op.create_index('idx_applicants_tax_id_hash', 'applicants', ['tax_id_hash'], unique=False)

    # 2. Assessments Table
    op.create_table('assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED', 'FAILED_PROCESSING')", name='chk_status'),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_assessments_applicant_id', 'assessments', ['applicant_id'], unique=False)
    op.create_index('idx_assessments_features_gin', 'assessments', ['input_features'], unique=False, postgresql_using='gin')

    # 3. Rule Registry
    op.create_table('rule_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('engine_id', sa.String(length=50), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('logic_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('engine_id', 'version', name='uq_rule_engine_version')
    )
    op.create_index('idx_active_rules', 'rule_registry', ['engine_id'], unique=False, postgresql_where=sa.text('is_active = TRUE'))

    # 4. Model Registry
    op.create_table('model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('engine_id', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=20), nullable=False),
        sa.Column('artifact_s3_uri', sa.String(length=512), nullable=False),
        sa.Column('training_data_hash', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('engine_id', 'model_version', name='uq_model_engine_version')
    )
    op.create_index('idx_active_models', 'model_registry', ['engine_id'], unique=False, postgresql_where=sa.text('is_active = TRUE'))

    # 5. Archetype Results
    op.create_table('archetype_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('archetype_label', sa.String(length=100), nullable=False),
        sa.Column('cluster_distances', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['model_registry.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id')
    )
    op.create_index('idx_archetype_assessment', 'archetype_results', ['assessment_id'], unique=False)

    # 6. Recommendation Results
    op.create_table('recommendation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('suggested_limit', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('improvement_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['model_registry.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id')
    )
    op.create_index('idx_recommendation_assessment', 'recommendation_results', ['assessment_id'], unique=False)

    # 7. Audit Log
    op.create_table('audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_id', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('logged_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_assessment_id', 'audit_log', ['assessment_id'], unique=False)
    op.create_index('idx_audit_correlation_id', 'audit_log', ['correlation_id'], unique=False)
    op.create_index('idx_audit_logged_at', 'audit_log', ['logged_at'], unique=False)

    # Immutable Audit Log Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Updates to the audit_log table are strictly prohibited for compliance reasons.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_prevent_audit_update
        BEFORE UPDATE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_update();
    """)


def downgrade() -> None:
    # Drop Audit Trigger
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_update ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_update();")

    # Drop Tables
    op.drop_table('audit_log')
    op.drop_table('recommendation_results')
    op.drop_table('archetype_results')
    op.drop_table('model_registry')
    op.drop_table('rule_registry')
    op.drop_table('assessments')
    op.drop_table('applicants')
