"""Architecture reconciliation

Revision ID: 003
Revises: 002
Create Date: 2026-06-14 23:38:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Drop redundant/derived physical columns
    op.drop_column('optimization_results', 'emi_shortfall')
    op.drop_column('application_sessions', 'fo_retry_count')
    op.drop_column('application_sessions', 'aa_retry_count')

    # 2. Add formally documented contract_emi
    op.add_column('optimization_results', sa.Column('contract_emi', sa.Integer(), server_default='0', nullable=False))

def downgrade() -> None:
    # 1. Drop contract_emi
    op.drop_column('optimization_results', 'contract_emi')

    # 2. Restore legacy derived columns
    op.add_column('application_sessions', sa.Column('aa_retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('application_sessions', sa.Column('fo_retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('optimization_results', sa.Column('emi_shortfall', sa.Integer(), server_default='0', nullable=False))
