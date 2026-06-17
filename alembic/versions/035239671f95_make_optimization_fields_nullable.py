"""make_optimization_fields_nullable

Revision ID: 035239671f95
Revises: fe5350529b37
Create Date: 2026-06-15 03:12:16.766655

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '035239671f95'
down_revision = 'fe5350529b37'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('optimization_results', 'approved_loan_amount', existing_type=sa.Integer(), nullable=True)
    op.alter_column('optimization_results', 'approved_tenure', existing_type=sa.Integer(), nullable=True)

def downgrade() -> None:
    op.execute("UPDATE optimization_results SET approved_loan_amount = 1000 WHERE approved_loan_amount IS NULL")
    op.execute("UPDATE optimization_results SET approved_tenure = 12 WHERE approved_tenure IS NULL")
    op.alter_column('optimization_results', 'approved_loan_amount', existing_type=sa.Integer(), nullable=False)
    op.alter_column('optimization_results', 'approved_tenure', existing_type=sa.Integer(), nullable=False)
