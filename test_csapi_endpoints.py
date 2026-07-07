"""Diagnostic: probe every Capital Stake endpoint used by the backend."""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("CAPITAL_STAKE_UAT_TOKEN", "")
BASE = "https://uat.csapis.com/3.0"
TICKER = "OGDC"


async def get(client: httpx.AsyncClient, path: str, params: dict = None) -> None:
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    url = BASE + path
    try:
        r = await client.get(url, params=params, headers=headers)
        body = r.text[:300].replace("\n", " ")
        print(f"  [{r.status_code}] {path} {params or ''}")
        if r.status_code != 200:
            print(f"         BODY: {body}")
        else:
            print(f"         OK: {body[:120]}")
    except Exception as exc:
        print(f"  [ERR] {path}: {exc}")


async def main() -> None:
    async with httpx.AsyncClient(timeout=20) as c:
        print("=== Market / Ticker endpoints ===")
        await get(c, "/market/tickers")
        await get(c, "/market/state")
        await get(c, "/market/sectors")
        await get(c, "/market/stock", {"symbol": TICKER})
        await get(c, "/market/eod-adj", {"symbol": TICKER, "from": "2024-01-01", "to": "2024-01-31"})
        await get(c, "/market/technicals", {"symbol": TICKER, "interval": "1d"})
        await get(c, "/market/sectors/stocks", {"sector_code": "E&P"})
        await get(c, "/market/sector/stocks", {"sector_code": "E&P"})

        print("\n=== Company endpoints ===")
        await get(c, "/company/shareholders", {"symbol": TICKER})
        await get(c, "/company/financials/income/annual", {"symbol": TICKER})
        await get(c, "/company/financials/income/quarterly", {"symbol": TICKER})
        await get(c, "/company/financials/balance/annual", {"symbol": TICKER})
        await get(c, "/company/financials/cashflow/annual", {"symbol": TICKER})

        print("\n=== News endpoints ===")
        await get(c, "/news/company", {"symbol": TICKER})
        await get(c, "/news/sector", {"sector_code": "0801"})

        print("\n=== Payouts endpoints ===")
        await get(c, "/payouts/dividends", {"symbol": TICKER})

        print("\n=== Research endpoints ===")
        await get(c, "/research/targets", {"symbol": TICKER})
        await get(c, "/research/consensus", {"symbol": TICKER})


if __name__ == "__main__":
    asyncio.run(main())
