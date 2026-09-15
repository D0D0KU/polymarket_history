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
    ankr_key: str

    # Wallet
    wallet: str

    # Scanner
    start_block: int = 80_813_428
    chunk_size: int = 1000

    # Contracts
    pusd_address: str = (
        "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"
    )

    ctf_address: str = (
        "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
    )

    @property
    def rpc_url(self) -> str:
        return f"https://rpc.ankr.com/polygon/{self.ankr_key}"


settings = Settings()
