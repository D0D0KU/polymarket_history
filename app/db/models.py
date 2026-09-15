from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WalletEvent(Base):
    __tablename__ = "wallet_events"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    wallet: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    token_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )

    block_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    tx_hash: Mapped[str] = mapped_column(
        String(66),
        nullable=False,
    )

    log_index: Mapped[int] = mapped_column(
        nullable=False,
    )

    from_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )

    to_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )

    token_id: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    amount_raw: Mapped[int] = mapped_column(
        Numeric(78, 0),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(78, 18),
        nullable=False,
    )

    direction: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tx_hash",
            "log_index",
            "event_type",
            "token_id",
            name="uq_wallet_event",
        ),

        Index(
            "idx_wallet_events_block",
            "block_number",
        ),

        Index(
            "idx_wallet_events_wallet",
            "wallet",
        ),

        Index(
            "idx_wallet_events_token",
            "token",
        ),
    )


class WalletBalance(Base):
    __tablename__ = "wallet_balances"

    wallet: Mapped[str] = mapped_column(
        String(42),
        primary_key=True,
    )

    token: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )

    token_address: Mapped[str] = mapped_column(
        String(42),
        primary_key=True,
    )

    token_id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
        default="",
    )

    balance_raw: Mapped[int] = mapped_column(
        Numeric(78, 0),
        nullable=False,
    )

    balance: Mapped[float] = mapped_column(
        Numeric(78, 18),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class WalletBalanceOnchain(Base):
    __tablename__ = "wallet_balances_onchain"

    wallet: Mapped[str] = mapped_column(
        String(42),
        primary_key=True,
    )

    token: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )

    token_address: Mapped[str] = mapped_column(
        String(42),
        primary_key=True,
    )

    token_id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
        default="",
    )

    balance_raw: Mapped[int] = mapped_column(
        Numeric(78, 0),
        nullable=False,
    )

    balance: Mapped[float] = mapped_column(
        Numeric(78, 18),
        nullable=False,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class WalletSync(Base):
    __tablename__ = "wallet_syncs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    wallet: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )

    block_from: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    block_to: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    events_count: Mapped[int] = mapped_column(
        nullable=False,
    )

    pusd_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    ctf_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    all_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
