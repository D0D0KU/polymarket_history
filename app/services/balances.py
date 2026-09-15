from collections import defaultdict
from decimal import Decimal

from web3 import Web3
from sqlalchemy.orm import Session

from app.blockchain.abis import ERC20_ABI, ERC1155_ABI
from app.blockchain.client import w3
from app.config import settings
from app.db.models import (
    WalletBalance,
    WalletBalanceOnchain,
    WalletEvent,
)


DECIMALS = 6
CTF_BATCH_SIZE = 100


def human(raw: int) -> Decimal:
    return Decimal(raw) / Decimal(10**DECIMALS)


def balances_from_events(
    events: list[dict],
) -> dict[tuple[str, str, str], int]:
    balances: dict[tuple[str, str, str], int] = defaultdict(int)

    for event in events:
        key = (
            event["token"],
            event["token_address"].lower(),
            event.get("token_id") or "",
        )
        raw = int(event["amount_raw"])
        if event["dir"] == "in":
            balances[key] += raw
        elif event["dir"] == "out":
            balances[key] -= raw

    for token, address in settings.erc20_tokens:
        balances.setdefault((token, address.lower(), ""), 0)

    return dict(balances)


def balances_from_db(session: Session) -> dict[tuple[str, str, str], int]:
    rows = (
        session.query(WalletEvent)
        .filter(WalletEvent.wallet == settings.wallet.lower())
        .all()
    )
    events = [
        {
            "token": row.token,
            "token_address": row.token_address,
            "token_id": row.token_id or "",
            "amount_raw": int(row.amount_raw),
            "dir": row.direction,
        }
        for row in rows
    ]
    return balances_from_events(events)


def ctf_token_ids_from_db(session: Session) -> list[str]:
    rows = (
        session.query(WalletEvent.token_id)
        .filter(
            WalletEvent.wallet == settings.wallet.lower(),
            WalletEvent.token == "CTF",
            WalletEvent.token_id != "",
        )
        .distinct()
        .all()
    )
    return [row[0] for row in rows]


def balances_onchain(block: int, token_ids: list[str]) -> dict:
    wallet = Web3.to_checksum_address(settings.wallet)
    result: dict[tuple[str, str, str], int] = {}

    for token, address in settings.erc20_tokens:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=ERC20_ABI,
        )
        raw = contract.functions.balanceOf(wallet).call(
            block_identifier=block
        )
        result[(token, address.lower(), "")] = int(raw)

    if not token_ids:
        return result

    ctf = w3.eth.contract(
        address=Web3.to_checksum_address(settings.ctf_address),
        abi=ERC1155_ABI,
    )
    ctf_address = settings.ctf_address.lower()
    ids = [str(token_id) for token_id in token_ids]

    for offset in range(0, len(ids), CTF_BATCH_SIZE):
        chunk = ids[offset : offset + CTF_BATCH_SIZE]
        accounts = [wallet] * len(chunk)
        values = ctf.functions.balanceOfBatch(
            accounts,
            [int(token_id) for token_id in chunk],
        ).call(block_identifier=block)
        for token_id, raw in zip(chunk, values):
            result[("CTF", ctf_address, token_id)] = int(raw)

    return result


def save_historical_balances(session: Session, balances: dict) -> None:
    wallet = settings.wallet.lower()
    for (token, token_address, token_id), raw in balances.items():
        session.merge(
            WalletBalance(
                wallet=wallet,
                token=token,
                token_address=token_address,
                token_id=token_id,
                balance_raw=raw,
                balance=human(raw),
            )
        )
    session.commit()


def save_onchain_balances(session: Session, balances: dict) -> None:
    wallet = settings.wallet.lower()
    for (token, token_address, token_id), raw in balances.items():
        session.merge(
            WalletBalanceOnchain(
                wallet=wallet,
                token=token,
                token_address=token_address,
                token_id=token_id,
                balance_raw=raw,
                balance=human(raw),
            )
        )
    session.commit()


def compare_balances(
    historical: dict,
    onchain: dict,
) -> list[dict]:
    keys = set(historical) | set(onchain)
    result = []
    for key in sorted(keys):
        historical_raw = int(historical.get(key, 0))
        onchain_raw = int(onchain.get(key, 0))
        result.append(
            {
                "token": key[0],
                "token_address": key[1],
                "token_id": key[2],
                "historical_raw": historical_raw,
                "onchain_raw": onchain_raw,
                "match": historical_raw == onchain_raw,
            }
        )
    return result
