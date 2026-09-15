from typing import Any

from web3 import Web3

from app.blockchain.client import w3
from app.config import settings


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


def get_logs(
    from_b: int,
    to_b: int,
    address: str,
    topics: list,
) -> list:

    try:
        return w3.eth.get_logs(
            {
                "fromBlock": from_b,
                "toBlock": to_b,
                "address": Web3.to_checksum_address(address),
                "topics": topics,
            }
        )

    except Exception as exc:

        if to_b - from_b <= 0:
            print(
                f"RPC error {from_b}-{to_b}: {exc}"
            )
            return []

        mid = (from_b + to_b) // 2

        print(
            f"RPC error {from_b}-{to_b}: {exc}"
        )

        print(
            f"Splitting at {mid}"
        )

        return (
            get_logs(
                from_b,
                mid,
                address,
                topics,
            )
            +
            get_logs(
                mid + 1,
                to_b,
                address,
                topics,
            )
        )


def fetch_pusd(
    start: int,
    end: int,
) -> list[dict]:

    events = []

    wallet_topic = topic_addr(settings.wallet)

    signature = topic_sig(
        "Transfer(address,address,uint256)"
    )

    queries = [
        [signature, wallet_topic, None],
        [signature, None, wallet_topic],
    ]

    for topics in queries:

        current = start

        while current <= end:

            to_block = min(
                current + settings.chunk_size - 1,
                end,
            )

            logs = get_logs(
                current,
                to_block,
                settings.pusd_address,
                topics,
            )

            contract = w3.eth.contract(
                address=Web3.to_checksum_address(
                    settings.pusd_address
                ),
                abi=[
                    {
                        "anonymous": False,
                        "inputs": [
                            {
                                "indexed": True,
                                "name": "from",
                                "type": "address",
                            },
                            {
                                "indexed": True,
                                "name": "to",
                                "type": "address",
                            },
                            {
                                "indexed": False,
                                "name": "value",
                                "type": "uint256",
                            },
                        ],
                        "name": "Transfer",
                        "type": "event",
                    }
                ],
            )

            for log in logs:

                try:
                    args = (
                        contract.events.Transfer()
                        .process_log(log)["args"]
                    )
                except Exception:
                    continue

                raw = int(args["value"])

                events.append(
                    {
                        "type": "erc20",
                        "token": "pUSD",
                        "token_address": settings.pusd_address,
                        "block": log["blockNumber"],
                        "tx": hx(log["transactionHash"]),
                        "log_index": log["logIndex"],
                        "from": args["from"],
                        "to": args["to"],
                        "amount_raw": raw,
                        "dir": (
                            "in"
                            if args["to"].lower()
                            == settings.wallet.lower()
                            else "out"
                        ),
                    }
                )

            current = to_block + 1

    print(f" pUSD pass done → {end}")

    return events


def fetch_ctf(
    start: int,
    end: int,
) -> list[dict]:

    events = []

    wallet_topic = topic_addr(settings.wallet)

    single = topic_sig(
        "TransferSingle(address,address,address,uint256,uint256)"
    )

    batch = topic_sig(
        "TransferBatch(address,address,address,uint256[],uint256[])"
    )

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(
            settings.ctf_address
        ),
        abi=[
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "name": "operator",
                        "type": "address",
                    },
                    {
                        "indexed": True,
                        "name": "from",
                        "type": "address",
                    },
                    {
                        "indexed": True,
                        "name": "to",
                        "type": "address",
                    },
                    {
                        "indexed": False,
                        "name": "id",
                        "type": "uint256",
                    },
                    {
                        "indexed": False,
                        "name": "value",
                        "type": "uint256",
                    },
                ],
                "name": "TransferSingle",
                "type": "event",
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "name": "operator",
                        "type": "address",
                    },
                    {
                        "indexed": True,
                        "name": "from",
                        "type": "address",
                    },
                    {
                        "indexed": True,
                        "name": "to",
                        "type": "address",
                    },
                    {
                        "indexed": False,
                        "name": "ids",
                        "type": "uint256[]",
                    },
                    {
                        "indexed": False,
                        "name": "values",
                        "type": "uint256[]",
                    },
                ],
                "name": "TransferBatch",
                "type": "event",
            },
        ],
    )

    queries = [
        (
            single,
            [single, None, wallet_topic, None],
            True,
        ),
        (
            single,
            [single, None, None, wallet_topic],
            True,
        ),
        (
            batch,
            [batch, None, wallet_topic, None],
            False,
        ),
        (
            batch,
            [batch, None, None, wallet_topic],
            False,
        ),
    ]

    for signature, topics, is_single in queries:

        current = start

        while current <= end:

            to_block = min(
                current + settings.chunk_size - 1,
                end,
            )

            logs = get_logs(
                current,
                to_block,
                settings.ctf_address,
                topics,
            )

            for log in logs:

                try:

                    if is_single:

                        args = (
                            contract.events.TransferSingle()
                            .process_log(log)["args"]
                        )

                        items = [
                            (
                                int(args["id"]),
                                int(args["value"]),
                            )
                        ]

                    else:

                        args = (
                            contract.events.TransferBatch()
                            .process_log(log)["args"]
                        )

                        items = list(
                            zip(
                                map(int, args["ids"]),
                                map(int, args["values"]),
                            )
                        )

                    from_address = args["from"]
                    to_address = args["to"]

                except Exception:
                    continue

                direction = (
                    "in"
                    if to_address.lower()
                    == settings.wallet.lower()
                    else "out"
                )

                for token_id, raw in items:

                    events.append(
                        {
                            "type": "erc1155",
                            "token": "CTF",
                            "token_address": settings.ctf_address,
                            "block": log["blockNumber"],
                            "tx": hx(log["transactionHash"]),
                            "log_index": log["logIndex"],
                            "from": from_address,
                            "to": to_address,
                            "token_id": str(token_id),
                            "amount_raw": raw,
                            "dir": direction,
                        }
                    )

            current = to_block + 1

    print(f" CTF pass done → {end}")

    return events


def scan_blocks() -> list[dict]:

    latest_block = w3.eth.block_number

    print(f"Latest block: {latest_block}")

    pusd_events = fetch_pusd(
        settings.start_block,
        latest_block,
    )

    ctf_events = fetch_ctf(
        settings.start_block,
        latest_block,
    )

    events = pusd_events + ctf_events
    
    unique = {}

    for event in events:

        key = (
            event["tx"].lower(),
            event["log_index"],
            event["token"],
            event.get("token_id", ""),
        )

        unique[key] = event

    return list(unique.values())
