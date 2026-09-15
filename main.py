import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert

from app.blockchain.client import check_connection, w3
from app.blockchain.scanner import scan_chunk
from app.config import settings
from app.db.database import SessionLocal
from app.db.models import WalletEvent
from app.services.balances import (
    balances_from_db,
    balances_onchain,
    compare_balances,
    ctf_token_ids_from_db,
    save_historical_balances,
    save_onchain_balances,
)
from app.services.sync import (
    resolve_from_block,
    save_progress,
    save_sync,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def save_events(events: list[dict]) -> int:
    if not events:
        return 0

    rows = []
    for event in events:
        rows.append(
            {
                "wallet": settings.wallet.lower(),
                "event_type": event["type"],
                "token": event["token"],
                "token_address": event["token_address"].lower(),
                "block_number": event["block"],
                "tx_hash": event["tx"].lower(),
                "log_index": event["log_index"],
                "from_address": event["from"].lower(),
                "to_address": event["to"].lower(),
                "token_id": event.get("token_id") or "",
                "amount_raw": event["amount_raw"],
                "amount": Decimal(event["amount_raw"]) / Decimal(10**6),
                "direction": event["dir"],
            }
        )

    with SessionLocal() as session:
        stmt = insert(WalletEvent).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_wallet_event",
            set_={
                "wallet": stmt.excluded.wallet,
                "token": stmt.excluded.token,
                "token_address": stmt.excluded.token_address,
                "block_number": stmt.excluded.block_number,
                "from_address": stmt.excluded.from_address,
                "to_address": stmt.excluded.to_address,
                "amount_raw": stmt.excluded.amount_raw,
                "amount": stmt.excluded.amount,
                "direction": stmt.excluded.direction,
            },
        )
        session.execute(stmt)
        session.commit()

    return len(rows)


def main() -> int:
    logger.info(
        "Starting Polymarket wallet history restore..."
    )
    check_connection()

    started_at = datetime.now(timezone.utc)
    to_block = int(w3.eth.block_number)

    with SessionLocal() as session:
        from_block = resolve_from_block(session)

    logger.info("Pinned block: %s", to_block)
    logger.info(
        "Scan range: %s → %s",
        from_block,
        to_block,
    )

    events_saved = 0

    if from_block <= to_block:
        current = from_block
        while current <= to_block:
            chunk_end = min(
                current + settings.chunk_size - 1,
                to_block,
            )
            events = scan_chunk(current, chunk_end)
            events_saved += save_events(events)
            with SessionLocal() as session:
                save_progress(session, chunk_end)
            logger.info(
                "Scanned %s/%s (%s events in chunk)",
                chunk_end,
                to_block,
                len(events),
            )
            current = chunk_end + 1
    else:
        logger.info(
            "Already synced through pinned block."
        )

    with SessionLocal() as session:
        historical_balances = balances_from_db(
            session
        )
        token_ids = ctf_token_ids_from_db(
            session
        )

        onchain_balances = balances_onchain(
            to_block,
            token_ids
        )
        comparison = compare_balances(
            historical_balances,
            onchain_balances,
        )

        save_historical_balances(
            session,
            historical_balances
        )
        save_onchain_balances(
            session, onchain_balances
        )
        save_sync(
            session,
            from_block if from_block <= to_block else to_block,
            to_block,
            events_saved,
            comparison,
            started_at,
        )

    logger.info(
        "Balance comparison at block %s:", to_block
    )

    all_match = True
    for item in comparison:
        all_match = all_match and item["match"]
        logger.info(
            "%s %s: historical=%s onchain=%s match=%s",
            item["token"],
            item["token_id"] or "-",
            item["historical_raw"],
            item["onchain_raw"],
            item["match"],
        )

    if all_match:
        logger.info("Done. All balances match.")
        return 0

    mismatches = [
        item for item in comparison if not item["match"]
    ]
    logger.warning(
        "%s balance(s) did not match at block %s.",
        len(mismatches),
        to_block,
    )
    for item in mismatches:
        logger.warning(
            "%s %s historical=%s onchain=%s",
            item["token"],
            item["token_id"] or "-",
            item["historical_raw"],
            item["onchain_raw"],
        )
    logger.warning("Done. Balance mismatch.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
