from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import WalletScanProgress, WalletSync


def resolve_from_block(session: Session) -> int:
    wallet = settings.wallet.lower()
    progress = session.get(WalletScanProgress, wallet)
    if (
        progress is not None
        and progress.origin_block == settings.start_block
    ):
        return progress.last_block + 1
    return settings.start_block


def save_progress(session: Session, last_block: int) -> None:
    wallet = settings.wallet.lower()
    progress = session.get(WalletScanProgress, wallet)
    if progress is None:
        session.add(
            WalletScanProgress(
                wallet=wallet,
                origin_block=settings.start_block,
                last_block=last_block,
            )
        )
    else:
        progress.origin_block = settings.start_block
        progress.last_block = last_block
    session.commit()


def save_sync(
    session: Session,
    block_from: int,
    block_to: int,
    events_count: int,
    comparison: list[dict],
    started_at: datetime,
) -> None:
    def matched(token: str) -> bool:
        items = [
            item for item in comparison if item["token"] == token
        ]
        return all(item["match"] for item in items)

    session.add(
        WalletSync(
            wallet=settings.wallet.lower(),
            block_from=block_from,
            block_to=block_to,
            events_count=events_count,
            pusd_match=matched("pUSD"),
            usdce_match=matched("USDC.e"),
            ctf_match=matched("CTF"),
            all_match=all(item["match"] for item in comparison),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
    )
    session.commit()
