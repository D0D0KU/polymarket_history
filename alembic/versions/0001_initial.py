"""initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "wallet_events",

        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "wallet",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(32),
            nullable=False,
        ),

        sa.Column(
            "token",
            sa.String(32),
            nullable=False,
        ),

        sa.Column(
            "token_address",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "block_number",
            sa.BigInteger(),
            nullable=False,
        ),

        sa.Column(
            "tx_hash",
            sa.String(66),
            nullable=False,
        ),

        sa.Column(
            "log_index",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "from_address",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "to_address",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "token_id",
            sa.String(80),
            nullable=True,
        ),

        sa.Column(
            "amount_raw",
            sa.Numeric(78, 0),
            nullable=False,
        ),

        sa.Column(
            "amount",
            sa.Numeric(78, 18),
            nullable=False,
        ),

        sa.Column(
            "direction",
            sa.String(8),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "tx_hash",
            "log_index",
            "event_type",
            "token_id",
            name="uq_wallet_event",
        ),
    )

    op.create_index(
        "idx_wallet_events_block",
        "wallet_events",
        ["block_number"],
    )

    op.create_index(
        "idx_wallet_events_wallet",
        "wallet_events",
        ["wallet"],
    )

    op.create_index(
        "idx_wallet_events_token",
        "wallet_events",
        ["token"],
    )


    op.create_table(
        "wallet_balances",

        sa.Column(
            "wallet",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "token",
            sa.String(32),
            nullable=False,
        ),

        sa.Column(
            "token_address",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "token_id",
            sa.String(80),
            nullable=False,
            server_default="",
        ),

        sa.Column(
            "balance_raw",
            sa.Numeric(78, 0),
            nullable=False,
        ),

        sa.Column(
            "balance",
            sa.Numeric(78, 18),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "wallet",
            "token",
            "token_address",
            "token_id",
        ),
    )


    op.create_table(
        "wallet_balances_onchain",

        sa.Column(
            "wallet",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "token",
            sa.String(32),
            nullable=False,
        ),

        sa.Column(
            "token_address",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "token_id",
            sa.String(80),
            nullable=False,
            server_default="",
        ),

        sa.Column(
            "balance_raw",
            sa.Numeric(78, 0),
            nullable=False,
        ),

        sa.Column(
            "balance",
            sa.Numeric(78, 18),
            nullable=False,
        ),

        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "wallet",
            "token",
            "token_address",
            "token_id",
        ),
    )


    op.create_table(
        "wallet_syncs",

        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "wallet",
            sa.String(42),
            nullable=False,
        ),

        sa.Column(
            "block_from",
            sa.BigInteger(),
            nullable=False,
        ),

        sa.Column(
            "block_to",
            sa.BigInteger(),
            nullable=False,
        ),

        sa.Column(
            "events_count",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "pusd_match",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "ctf_match",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "all_match",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:

    op.drop_table("wallet_syncs")

    op.drop_table("wallet_balances_onchain")

    op.drop_table("wallet_balances")

    op.drop_index(
        "idx_wallet_events_token",
        table_name="wallet_events",
    )

    op.drop_index(
        "idx_wallet_events_wallet",
        table_name="wallet_events",
    )

    op.drop_index(
        "idx_wallet_events_block",
        table_name="wallet_events",
    )

    op.drop_table("wallet_events")
