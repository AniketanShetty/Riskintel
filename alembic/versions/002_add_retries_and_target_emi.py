"""Add retries and target_emi

Revision ID: 002
Revises: 001
Create Date: 2026-06-14 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_v2_init'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add verification fallback counters to application_sessions
    op.add_column('application_sessions', sa.Column('aa_retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('application_sessions', sa.Column('fo_retry_count', sa.Integer(), server_default='0', nullable=False))

    # Add target_emi to optimization_results
    op.add_column('optimization_results', sa.Column('target_emi', sa.Integer(), server_default='0', nullable=False))

def downgrade() -> None:
    # Remove columns
    op.drop_column('optimization_results', 'target_emi')
    op.drop_column('application_sessions', 'fo_retry_count')
    op.drop_column('application_sessions', 'aa_retry_count')
