"""Diagnostic script: test Capital Stake UAT API authentication methods."""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("CAPITAL_STAKE_UAT_TOKEN", "")
BASE = "https://uat.csapis.com/3.0"
ENDPOINT = "/market/tickers"


async def probe(label: str, headers: dict) -> None:
    safe_headers = {k: (v[:8] + "..." if k.lower() == "authorization" else v) for k, v in headers.items()}
    print(f"\n--- {label} ---")
    print(f"Headers sent: {safe_headers}")
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(BASE + ENDPOINT, headers=headers)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text[:400]}")
        except Exception as exc:
            print(f"Exception: {exc}")


async def main() -> None:
    if not TOKEN:
        print("ERROR: CAPITAL_STAKE_UAT_TOKEN not set in .env")
        return

    print(f"Token length: {len(TOKEN)} chars")
    print(f"Base URL: {BASE}")
    print(f"Endpoint: {ENDPOINT}")

    await probe("1. Bearer (raw base64 token)", {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    })
    await probe("2. Basic (raw base64 token)", {
        "Authorization": f"Basic {TOKEN}",
        "Accept": "application/json",
    })
    await probe("3. Token header", {
        "Token": TOKEN,
        "Accept": "application/json",
    })
    await probe("4. X-API-Key header", {
        "X-API-Key": TOKEN,
        "Accept": "application/json",
    })
    await probe("5. No auth", {
        "Accept": "application/json",
    })
    # Also test market/state which is simpler
    print("\n\n=== Testing /market/state ===")
    await probe("Bearer on /market/state", {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    })


if __name__ == "__main__":
    asyncio.run(main())
