from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    database_url: str

    # Polygon / Ankr
    rpc_url: str
    ankr_key: str

    # Wallet
    wallet: str

    # Scanner
    start_block: int = 80_813_428
    chunk_size: int = 100
    rpc_retries: int = 8

    # Contracts
    pusd_address: str = (
        "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"
    )
    usdce_address: str = (
        "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    )
    ctf_address: str = (
        "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
    )

    @property
    def rpc_endpoint(self) -> str:
        return f"{self.rpc_url.rstrip('/')}/{self.ankr_key}"

    @property
    def erc20_tokens(self) -> list[tuple[str, str]]:
        return [
            ("pUSD", self.pusd_address),
            ("USDC.e", self.usdce_address),
        ]


settings = Settings()
