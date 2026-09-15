# Polymarket Wallet History

A tool for restoring Polymarket wallet transaction history from the Polygon blockchain and storing the data in PostgreSQL.

The project uses Ankr as the Polygon RPC provider.

## Requirements

* Docker
* Docker Compose
* Ankr API key

## 1. Get an ANKR_KEY

An **Ankr API key is required** to connect to the Polygon RPC.

You can get an API key from the official Ankr RPC platform:

[Ankr RPC](https://www.ankr.com/rpc/?utm_source=chatgpt.com)

Create an account, create an RPC project, and obtain your API key.

## 2. Configure `.env`

Create a `.env` file in the project root:

```env
ANKR_KEY=your_ankr_api_key

WALLET=0x46b353667fd7d846af3bbeda6584b0e5b883d3de

POSTGRES_DB=polymarket
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5435

START_BLOCK=80813428
CHUNK_SIZE=100
```

## 3. Run

Build and start the project:

```bash
docker compose up --build
```

The application will:

1. Start PostgreSQL.
2. Run Alembic migrations.
3. Connect to Polygon through Ankr.
4. Scan the wallet history.
5. Save wallet events to PostgreSQL.
6. Calculate historical balances.
7. Compare historical balances with current on-chain balances.

## 4. Stop

```bash
docker compose down
```

To remove the PostgreSQL database and all stored data:

```bash
docker compose down -v
```

> **Warning:** `-v` removes the PostgreSQL Docker volume and all database data.

## Configuration

| Variable            | Description                         |
| ------------------- | ----------------------------------- |
| `ANKR_KEY`          | Ankr API key                        |
| `WALLET`            | Polygon wallet address              |
| `POSTGRES_DB`       | PostgreSQL database name            |
| `POSTGRES_USER`     | PostgreSQL username                 |
| `POSTGRES_PASSWORD` | PostgreSQL password                 |
| `POSTGRES_PORT`     | PostgreSQL port                     |
| `START_BLOCK`       | Block number to start scanning from |
| `CHUNK_SIZE`        | Number of blocks per scan chunk     |
