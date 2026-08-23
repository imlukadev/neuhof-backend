"""create access logs

Revision ID: 0001_access_logs
Revises:
Create Date: 2026-08-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_access_logs"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referer", sa.Text(), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
    )
    op.create_index("ix_access_logs_accessed_at", "access_logs", ["accessed_at"])


def downgrade() -> None:
    op.drop_index("ix_access_logs_accessed_at", table_name="access_logs")
    op.drop_table("access_logs")
