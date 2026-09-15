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
)


DECIMALS = 6


def human(raw: int) -> Decimal:
    return Decimal(raw) / Decimal(10**DECIMALS)


def balances_from_events(
    events: list[dict],
) -> dict[tuple[str, str, str], int]:

    balances = defaultdict(int)

    for event in sorted(
        events,
        key=lambda x: (
            x["block"],
            x["log_index"],
        ),
    ):

        token = event["token"]

        token_address = event[
            "token_address"
        ].lower()

        token_id = event.get(
            "token_id",
            "",
        )

        key = (
            token,
            token_address,
            token_id,
        )

        raw = int(event["amount_raw"])

        if event["dir"] == "in":
            balances[key] += raw
        else:
            balances[key] -= raw

    return dict(balances)


def balances_onchain() -> dict:

    wallet = Web3.to_checksum_address(
        settings.wallet
    )

    result = {}

    pusd = w3.eth.contract(
        address=Web3.to_checksum_address(
            settings.pusd_address
        ),
        abi=ERC20_ABI,
    )

    raw = pusd.functions.balanceOf(
        wallet
    ).call()

    result[
        (
            "pUSD",
            settings.pusd_address.lower(),
            "",
        )
    ] = int(raw)

    return result


def balances_onchain_for_token_ids(
    token_ids: set[str],
) -> dict:

    wallet = Web3.to_checksum_address(
        settings.wallet
    )

    ctf = w3.eth.contract(
        address=Web3.to_checksum_address(
            settings.ctf_address
        ),
        abi=ERC1155_ABI,
    )

    result = {}

    for token_id in token_ids:

        raw = ctf.functions.balanceOf(
            wallet,
            int(token_id),
        ).call()

        result[
            (
                "CTF",
                settings.ctf_address.lower(),
                str(token_id),
            )
        ] = int(raw)

    return result


def save_historical_balances(
    session: Session,
    balances: dict,
) -> None:

    for (
        token,
        token_address,
        token_id,
    ), raw in balances.items():

        item = WalletBalance(
            wallet=settings.wallet.lower(),
            token=token,
            token_address=token_address,
            token_id=token_id,
            balance_raw=raw,
            balance=human(raw),
        )

        session.merge(item)

    session.commit()


def save_onchain_balances(
    session: Session,
    balances: dict,
) -> None:

    for (
        token,
        token_address,
        token_id,
    ), raw in balances.items():

        item = WalletBalanceOnchain(
            wallet=settings.wallet.lower(),
            token=token,
            token_address=token_address,
            token_id=token_id,
            balance_raw=raw,
            balance=human(raw),
        )

        session.merge(item)

    session.commit()


def compare_balances(
    historical: dict,
    onchain: dict,
) -> list[dict]:

    keys = set(historical) | set(onchain)

    result = []

    for key in sorted(keys):

        historical_raw = historical.get(
            key,
            0,
        )

        onchain_raw = onchain.get(
            key,
            0,
        )

        result.append(
            {
                "token": key[0],
                "token_address": key[1],
                "token_id": key[2],
                "historical_raw": historical_raw,
                "onchain_raw": onchain_raw,
                "match": (
                    historical_raw
                    == onchain_raw
                ),
            }
        )

    return result
