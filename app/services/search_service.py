"""Search service — S1, S2."""
from app.api.v1.schemas.search import SearchResult, SymbolSearchResponse
from app.core.memory_cache import get_memory_cache
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import _rows_from_list
from app.providers.capital_stake.psx_symbols import fallback_symbol_rows
from app.repositories.symbol_repository import SymbolRepository

_symbol_cache: list[dict] = []


class SearchService:
    def __init__(self, capital_stake: CapitalStakeClient, symbol_repo: SymbolRepository):
        self.capital_stake = capital_stake
        self.symbol_repo = symbol_repo
        self._cache = get_memory_cache()

    async def _get_universe(self) -> list[dict]:
        global _symbol_cache
        if _symbol_cache:
            return _symbol_cache
        cached = self._cache.get("search:universe")
        if cached:
            return cached[0]

        items: list[dict] = []
        if self.capital_stake.is_configured():
            try:
                raw = self.capital_stake._unwrap_data(await self.capital_stake.get_all_tickers())
                items = _rows_from_list(raw)
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

    async def search_symbols(self, query: str, exchange: str = "PSX", limit: int = 10) -> SymbolSearchResponse:
        q = query.strip().upper()
        if not q:
            return SymbolSearchResponse(query=query, results=[], total=0)

        universe = await self._get_universe()
        results: list[SearchResult] = []
        for item in universe:
            ticker = str(
                item.get("ticker", item.get("symbol", item.get("s", item.get("code", ""))))
            ).upper()
            if item.get("m") == "IDX":
                continue
            name = str(item.get("name", item.get("companyName", ticker)))
            if ticker.startswith(q) or q in name.upper():
                results.append(SearchResult(
                    ticker=ticker,
                    name=name,
                    exchange=str(item.get("exchange", exchange)),
                    type="stock",
                    currency=str(item.get("currency", "PKR")),
                ))
            if len(results) >= limit:
                break
        return SymbolSearchResponse(query=query, results=results, total=len(results))

    async def search_news(self, query: str, limit: int = 10) -> dict:
        return {"query": query, "articles": [], "total": 0}
