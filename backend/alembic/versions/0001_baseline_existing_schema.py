"""baseline: existing schema (no-op stamp)

Revision ID: 0001_baseline_existing_schema
Revises:
Create Date: 2026-06-06 18:40:00.000000

The canonical V1 backend manages its schema via `app.audit.init_db()`,
which creates the `audit_log` and `reports` tables (and the
`idx_reports_user_type_generated_at` index) on demand. This baseline
revision stamps the Alembic version table at `head` so future schema
changes can be applied via `alembic upgrade head` without disturbing
the existing tables or the rows already persisted across restarts.

This migration performs no DDL — it exists only to register a starting
point in the Alembic version history.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_baseline_existing_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: the runtime-managed `audit_log` and `reports` tables already
    # exist and are preserved exactly as-is. This revision only stamps
    # the Alembic version so subsequent schema work can build on it.
    pass


def downgrade() -> None:
    # No-op: nothing to undo for a baseline stamp.
    pass
