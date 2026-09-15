import logging
import time
from collections import defaultdict
from typing import Any

from web3 import Web3

from app.blockchain.abis import ERC20_ABI, ERC1155_ABI
from app.blockchain.client import w3
from app.config import settings

logger = logging.getLogger(__name__)


RANGE_HINTS = (
    "too large",
    "block range",
    "response size",
    "query returned more",
    "more than",
    "exceeds the max",
    "log response",
    "-32005",
)

ERC20_TRANSFER = "Transfer(address,address,uint256)"
CTF_SINGLE = (
    "TransferSingle(address,address,address,uint256,uint256)"
)
CTF_BATCH = (
    "TransferBatch(address,address,address,uint256[],uint256[])"
)


def hx(v: Any) -> str:
    s = v.hex() if hasattr(v, "hex") else str(v)
    s = s.lower()

    return s if s.startswith("0x") else "0x" + s


def topic_addr(addr: str) -> str:
    return (
        "0x"
        + "0" * 24
        + addr.lower().replace("0x", "")
    )


def topic_sig(sig: str) -> str:
    return hx(w3.keccak(text=sig))


def transfer_direction(from_addr: str, to_addr: str) -> str:
    wallet = settings.wallet.lower()
    source = from_addr.lower()
    dest = to_addr.lower()
    if source == wallet and dest == wallet:
        return "self"
    if dest == wallet:
        return "in"
    return "out"


def collapse_token_amounts(
    pairs: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    totals: dict[int, int] = defaultdict(int)
    order: list[int] = []
    for token_id, amount in pairs:
        if token_id not in totals:
            order.append(token_id)
        totals[token_id] += int(amount)
    return [
        (token_id, totals[token_id]) for token_id in order
    ]


def get_logs(
    from_b: int,
    to_b: int,
    address: str,
    topics: list,
) -> list:
    delay = 1.0
    last_exc: Exception | None = None
    payload = {
        "fromBlock": from_b,
        "toBlock": to_b,
        "address": Web3.to_checksum_address(address),
        "topics": topics,
    }

    for attempt in range(settings.rpc_retries):
        try:
            return list(w3.eth.get_logs(payload))
        except Exception as exc:
            last_exc = exc
            text = str(exc).lower()
            can_split = from_b < to_b and (
                "-32062" in text
                or any(hint in text for hint in RANGE_HINTS)
            )
            if can_split:
                mid = (from_b + to_b) // 2
                logger.warning(
                    "RPC range %s-%s, split at %s: %s",
                    from_b,
                    to_b,
                    mid,
                    exc,
                )
                return get_logs(
                    from_b, mid, address, topics
                ) + get_logs(
                    mid + 1, to_b, address, topics
                )
            logger.warning(
                "RPC retry %s/%s %s-%s: %s",
                attempt + 1,
                settings.rpc_retries,
                from_b,
                to_b,
                exc,
            )
            time.sleep(delay)
            delay = min(delay * 2, 30)

    raise RuntimeError(
        f"RPC getLogs failed {from_b}-{to_b} {address}: {last_exc}"
    ) from last_exc


def fetch_erc20(
    token: str,
    token_address: str,
    start: int,
    end: int,
) -> list[dict]:
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_address),
        abi=ERC20_ABI,
    )
    signature = topic_sig(ERC20_TRANSFER)
    wallet_topic = topic_addr(settings.wallet)
    events: list[dict] = []
    seen: set[tuple[str, int]] = set()

    for topics in (
        [signature, wallet_topic, None],
        [signature, None, wallet_topic],
    ):
        for log in get_logs(start, end, token_address, topics):
            key = (hx(log["transactionHash"]), int(log["logIndex"]))
            if key in seen:
                continue
            seen.add(key)

            args = contract.events.Transfer().process_log(log)["args"]
            events.append(
                {
                    "type": "erc20",
                    "token": token,
                    "token_address": token_address,
                    "block": int(log["blockNumber"]),
                    "tx": key[0],
                    "log_index": key[1],
                    "from": args["from"],
                    "to": args["to"],
                    "token_id": "",
                    "amount_raw": int(args["value"]),
                    "dir": transfer_direction(
                        args["from"],
                        args["to"],
                    ),
                }
            )

    return events


def fetch_ctf(start: int, end: int) -> list[dict]:
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(settings.ctf_address),
        abi=ERC1155_ABI,
    )
    wallet_topic = topic_addr(settings.wallet)
    single = topic_sig(CTF_SINGLE)
    batch = topic_sig(CTF_BATCH)
    events: list[dict] = []
    seen: set[tuple[str, int, str]] = set()

    queries = (
        (True, [single, None, wallet_topic, None]),
        (True, [single, None, None, wallet_topic]),
        (False, [batch, None, wallet_topic, None]),
        (False, [batch, None, None, wallet_topic]),
    )

    for is_single, topics in queries:
        for log in get_logs(
            start, end, settings.ctf_address, topics
        ):
            tx = hx(log["transactionHash"])
            log_index = int(log["logIndex"])

            if is_single:
                args = (
                    contract.events.TransferSingle()
                    .process_log(log)["args"]
                )
                items = [(int(args["id"]), int(args["value"]))]
            else:
                args = (
                    contract.events.TransferBatch()
                    .process_log(log)["args"]
                )
                items = collapse_token_amounts(
                    list(
                        zip(
                            map(int, args["ids"]),
                            map(int, args["values"]),
                        )
                    )
                )

            direction = transfer_direction(
                args["from"],
                args["to"],
            )

            for token_id, raw in items:
                key = (tx, log_index, str(token_id))
                if key in seen:
                    continue
                seen.add(key)
                events.append(
                    {
                        "type": "erc1155",
                        "token": "CTF",
                        "token_address": settings.ctf_address,
                        "block": int(log["blockNumber"]),
                        "tx": tx,
                        "log_index": log_index,
                        "from": args["from"],
                        "to": args["to"],
                        "token_id": str(token_id),
                        "amount_raw": raw,
                        "dir": direction,
                    }
                )

    return events


def scan_chunk(start: int, end: int) -> list[dict]:
    events: list[dict] = []
    for token, address in settings.erc20_tokens:
        events.extend(fetch_erc20(token, address, start, end))
    events.extend(fetch_ctf(start, end))
    return events
