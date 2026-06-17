"""Idempotency table

Revision ID: 005
Revises: 004
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'idempotency_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('idempotency_key', sa.String(64), nullable=False),
        sa.Column('route', sa.String(128), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('response_body', sa.Text(), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('idempotency_key', 'route', name='uq_idempotency_key_route'),
    )
    op.create_index('ix_idempotency_key', 'idempotency_records', ['idempotency_key'])


def downgrade() -> None:
    op.drop_index('ix_idempotency_key', table_name='idempotency_records')
    op.drop_table('idempotency_records')
