"""OptimizationResult versioning: drop UNIQUE(session_id), add attempt_number

Revision ID: 004
Revises: b854a5d4f03e
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = 'b854a5d4f03e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add attempt_number; default existing rows to 1 (they are all first-runs)
    op.add_column(
        'optimization_results',
        sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False)
    )

    # 2. Drop the old UNIQUE constraint on session_id alone.
    #    PostgreSQL names inline unique= columns as <table>_<col>_key.
    op.drop_constraint('optimization_results_session_id_key', 'optimization_results', type_='unique')

    # 3. Composite uniqueness: each (session, attempt) pair is unique.
    op.create_unique_constraint(
        'uq_optimization_attempt',
        'optimization_results',
        ['session_id', 'attempt_number']
    )


def downgrade() -> None:
    op.drop_constraint('uq_optimization_attempt', 'optimization_results', type_='unique')

    # Before restoring UNIQUE(session_id), delete all but the chronologically
    # first attempt row per session to prevent a UniqueViolation.
    # This is a lossy downgrade — later attempt rows are permanently deleted.
    from alembic import op as _op
    from sqlalchemy import text
    conn = _op.get_bind()
    conn.execute(text("""
        DELETE FROM optimization_results
        WHERE id NOT IN (
            SELECT DISTINCT ON (session_id) id
            FROM optimization_results
            ORDER BY session_id, attempt_number ASC
        )
    """))

    op.drop_column('optimization_results', 'attempt_number')
    op.create_unique_constraint(
        'optimization_results_session_id_key',
        'optimization_results',
        ['session_id']
    )
