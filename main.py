from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert

from app.blockchain.client import check_connection
from app.blockchain.scanner import scan_blocks
from app.config import settings
from app.db.database import SessionLocal
from app.db.models import WalletEvent
from app.services.balances import (
    balances_from_events,
    balances_onchain,
    balances_onchain_for_token_ids,
    compare_balances,
    save_historical_balances,
    save_onchain_balances,
)


def save_events(
    events: list[dict],
) -> None:

    if not events:
        return

    rows = []

    for event in events:

        rows.append(
            {
                "wallet": settings.wallet.lower(),
                "event_type": event["type"],
                "token": event["token"],
                "token_address": event[
                    "token_address"
                ].lower(),
                "block_number": event["block"],
                "tx_hash": event["tx"].lower(),
                "log_index": event["log_index"],
                "from_address": event[
                    "from"
                ].lower(),
                "to_address": event[
                    "to"
                ].lower(),
                "token_id": event.get(
                    "token_id",
                    "",
                ),
                "amount_raw": event[
                    "amount_raw"
                ],
                "amount": (
                    Decimal(
                        event["amount_raw"]
                    )
                    / Decimal(10**6)
                ),
                "direction": event["dir"],
            }
        )

    with SessionLocal() as session:

        stmt = insert(
            WalletEvent
        ).values(rows)

        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_wallet_event"
        )

        session.execute(stmt)

        session.commit()


def main() -> None:

    print(
        "Starting Polymarket wallet history restore..."
    )

    check_connection()

    events = scan_blocks()

    print(
        f"Parsed {len(events)} wallet events"
    )

    print("Saving events to PostgreSQL...")

    save_events(events)

    print("Events saved.")

    historical_balances = (
        balances_from_events(events)
    )

    onchain_balances = balances_onchain()

    ctf_token_ids = {
        event["token_id"]
        for event in events
        if (
            event["token"] == "CTF"
            and event.get("token_id")
        )
    }

    ctf_balances = (
        balances_onchain_for_token_ids(
            ctf_token_ids
        )
    )

    onchain_balances.update(
        ctf_balances
    )

    with SessionLocal() as session:

        save_historical_balances(
            session,
            historical_balances,
        )

        save_onchain_balances(
            session,
            onchain_balances,
        )

    comparison = compare_balances(
        historical_balances,
        onchain_balances,
    )

    print()
    print("Balance comparison:")
    print()

    for item in comparison:

        print(
            f"{item['token']} "
            f"{item['token_id'] or '-'}: "
            f"historical="
            f"{item['historical_raw']} "
            f"onchain="
            f"{item['onchain_raw']} "
            f"match="
            f"{item['match']}"
        )

    print()
    print("Done.")


if __name__ == "__main__":
    main()
