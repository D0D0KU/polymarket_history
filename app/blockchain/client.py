from web3 import Web3

from app.config import settings


w3 = Web3(
    Web3.HTTPProvider(
        settings.rpc_url,
        request_kwargs={
            "timeout": 60,
        },
    )
)


def check_connection() -> None:
    if not w3.is_connected():
        raise RuntimeError("Polygon RPC unavailable")
