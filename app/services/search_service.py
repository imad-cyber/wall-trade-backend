"""Search service — S1, S2."""
from __future__ import annotations

from typing import Any

from app.api.v1.schemas.search import SearchResult, SymbolSearchResponse
from app.core.memory_cache import get_memory_cache
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import _rows_from_list
from app.providers.capital_stake.psx_symbols import fallback_symbol_rows
from app.repositories.symbol_repository import SymbolRepository

_symbol_cache: list[dict[str, Any]] = []


def _normalize_ticker(item: dict[str, Any]) -> str:
    return str(
        item.get("ticker", item.get("symbol", item.get("s", item.get("code", ""))))
    ).upper().strip()


def _normalize_name(item: dict[str, Any], ticker: str) -> str:
    return str(
        item.get("name", item.get("companyName", item.get("company_name", ticker)))
    ).strip()


def _is_searchable_stock(item: dict[str, Any]) -> bool:
    if item.get("m") == "IDX":
        return False
    row_type = item.get("type")
    if row_type in (0, 2, "0", "2", "index", "IDX"):
        return False
    market_type = item.get("m")
    if market_type is not None and market_type not in (None, "REG", 1, "1"):
        return False
    ticker = _normalize_ticker(item)
    if not ticker or len(ticker) > 12:
        return False
    return True


def _match_score(query: str, ticker: str, name: str) -> int | None:
    name_upper = name.upper()
    if ticker == query:
        return 0
    if ticker.startswith(query):
        return 1
    if query in ticker:
        return 2
    if name_upper.startswith(query):
        return 3
    if query in name_upper:
        return 4
    return None


class SearchService:
    def __init__(self, capital_stake: CapitalStakeClient, symbol_repo: SymbolRepository):
        self.capital_stake = capital_stake
        self.symbol_repo = symbol_repo
        self._cache = get_memory_cache()

    async def _get_universe(self) -> list[dict[str, Any]]:
        global _symbol_cache
        if _symbol_cache:
            return _symbol_cache
        cached = self._cache.get("search:universe")
        if cached:
            _symbol_cache = cached[0]
            return cached[0]

        items: list[dict[str, Any]] = []
        if self.capital_stake.is_configured():
            try:
                raw = self.capital_stake._unwrap_data(await self.capital_stake.get_all_tickers())
                items = _rows_from_list(raw) if not isinstance(raw, list) else [
                    row for row in raw if isinstance(row, dict)
                ]
            except Exception:
                items = []
        if not items:
            try:
                items = self.symbol_repo.list(limit=5000)
            except Exception:
                items = []
        if not items:
            items = fallback_symbol_rows()

        _symbol_cache = items
        self._cache.set("search:universe", items, 86400)
        return items

    async def search_symbols(self, query: str, exchange: str = "PSX", limit: int = 25) -> SymbolSearchResponse:
        q = query.strip().upper()
        if not q:
            return SymbolSearchResponse(query=query, results=[], total=0)

        universe = await self._get_universe()
        ranked: list[tuple[int, str, SearchResult]] = []

        for item in universe:
            if not isinstance(item, dict) or not _is_searchable_stock(item):
                continue
            ticker = _normalize_ticker(item)
            name = _normalize_name(item, ticker)
            score = _match_score(q, ticker, name)
            if score is None:
                continue
            ranked.append(
                (
                    score,
                    ticker,
                    SearchResult(
                        ticker=ticker,
                        name=name,
                        exchange=str(item.get("exchange", exchange)),
                        type="stock",
                        currency=str(item.get("currency", "PKR")),
                    ),
                )
            )

        ranked.sort(key=lambda row: (row[0], row[1]))
        results = [row[2] for row in ranked[:limit]]
        return SymbolSearchResponse(query=query, results=results, total=len(results))

    async def search_news(self, query: str, limit: int = 10) -> dict:
        return {"query": query, "articles": [], "total": 0}
