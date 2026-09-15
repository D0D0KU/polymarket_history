"""add usdce match and scan progress

Revision ID: 0002_usdce_scan_progress
Revises: 0001_initial
Create Date: 2026-09-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_usdce_scan_progress"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE wallet_events SET token_id = '' WHERE token_id IS NULL"
    )
    op.alter_column(
        "wallet_events",
        "token_id",
        existing_type=sa.String(length=80),
        nullable=False,
        server_default="",
    )
    op.add_column(
        "wallet_syncs",
        sa.Column(
            "usdce_match",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_table(
        "wallet_scan_progress",
        sa.Column("wallet", sa.String(length=42), nullable=False),
        sa.Column("origin_block", sa.BigInteger(), nullable=False),
        sa.Column("last_block", sa.BigInteger(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("wallet"),
    )


def downgrade() -> None:
    op.drop_table("wallet_scan_progress")
    op.drop_column("wallet_syncs", "usdce_match")
    op.alter_column(
        "wallet_events",
        "token_id",
        existing_type=sa.String(length=80),
        nullable=True,
        server_default=None,
    )
