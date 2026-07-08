"""Market price service — M1 through M6."""
import asyncio
import json
from typing import Any, AsyncIterator, Optional

from app.api.v1.schemas.company import StockDataSchema
from app.api.v1.schemas.market import (
    MarketSummaryResponse,
    OHLCVResponse,
    OpexDatesResponse,
    PeerMetric,
    PeerMetricPositions,
    PeersComparisonResponse,
    RelatedTickersResponse,
)
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.memory_cache import get_memory_cache
from app.domain.market.models import Price
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import (
    _map_v3_market_state,
    _rows_from_list,
    compute_opex_dates,
    map_market_summary,
    map_ohlcv,
    map_related,
    validate_ohlcv_params,
)
from app.providers.capital_stake.v3_paths import lookback_days_for_range
from app.providers.psx_proxy.client import PSXProxyClient

QUOTE_CACHE_TTL = 60
OHLCV_CACHE_TTL = 3600
PEERS_CACHE_TTL = 21600
RELATED_CACHE_TTL = 86400
OPEX_CACHE_TTL = 86400
SUMMARY_CACHE_TTL = 60


class MarketService:
    def __init__(
        self,
        psx_client: PSXProxyClient,
        capital_stake: CapitalStakeClient | None = None,
    ):
        self.psx_client = psx_client
        self.capital_stake = capital_stake or CapitalStakeClient()
        self.settings = get_settings()
        self._cache = get_memory_cache()

    def is_configured(self) -> bool:
        return self.capital_stake.is_configured() or bool(self.settings.psx_proxy_base_url)

    def missing_config(self) -> list[str]:
        missing: list[str] = []
        if not self.capital_stake.is_configured():
            missing.append("CAPITAL_STAKE_UAT_TOKEN or CAPITAL_STAKE_API_KEY")
        return missing

    async def _cached(self, key: str, ttl: int, factory):
        cached = self._cache.get(key)
        if cached is not None:
            return cached[0], True, cached[1]
        if not self.capital_stake.is_configured():
            stale = self._cache.get_stale(key)
            if stale is not None:
                return stale[0], True, stale[1]
            raise ExternalServiceError(
                "Capital Stake", "API token not configured", error_code="SERVICE_UNAVAILABLE",
            )
        try:
            result = await factory()
        except ExternalServiceError:
            stale = self._cache.get_stale(key)
            if stale is not None:
                return stale[0], True, stale[1]
            raise
        self._cache.set(key, result, ttl)
        return result, False, 0

    async def get_quote(self, ticker: str) -> tuple[StockDataSchema, bool, int]:
        cache_key = f"market:quote:{ticker.upper()}"

        async def fetch():
            return await self.capital_stake.get_stock_quote(ticker)

        return await self._cached(cache_key, QUOTE_CACHE_TTL, fetch)

    async def get_ohlcv(
        self, ticker: str, range_: str = "2y", interval: str = "1d",
    ) -> tuple[OHLCVResponse, bool, int]:
        validate_ohlcv_params(range_, interval)
        cache_key = f"market:ohlcv:{ticker.upper()}:{range_}:{interval}"

        async def fetch():
            raw = self.capital_stake._unwrap_data(
                await self.capital_stake.get_eod_data(
                    ticker,
                    lookback_days=lookback_days_for_range(range_),
                )
            )
            return map_ohlcv(ticker, raw, range_, interval)

        return await self._cached(cache_key, OHLCV_CACHE_TTL, fetch)

    async def get_peers(self, ticker: str, category: str = "Value") -> tuple[PeersComparisonResponse, bool, int]:
        cache_key = f"market:peers:{ticker.upper()}:{category}"

        async def fetch():
            upper = ticker.upper()

            stock_raw = self.capital_stake._unwrap_data(
                await self.capital_stake.get_single_quote(upper)
            )
            sector_code = str(stock_raw.get("sector", "")).strip()

            peer_tickers: list[str] = []
            try:
                constituents_raw = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_index_constituents("KSE100", page=1)
                )
                items = _rows_from_list(constituents_raw) if not isinstance(constituents_raw, list) else [
                    row for row in constituents_raw if isinstance(row, dict)
                ]
                for item in items:
                    sym = str(item.get("symbol", item.get("ticker", ""))).upper()
                    item_sector = str(item.get("sector", ""))
                    if sym and sym != upper and item_sector == sector_code:
                        peer_tickers.append(sym)
                        if len(peer_tickers) >= 4:
                            break
            except ExternalServiceError:
                pass

            all_tickers = [upper] + peer_tickers
            results = await asyncio.gather(
                *[self.capital_stake.get_key_metrics_annual(t) for t in all_tickers],
                return_exceptions=True,
            )

            def extract_metrics(raw_result: Any) -> dict[str, float | None]:
                if isinstance(raw_result, Exception):
                    return {}
                data = self.capital_stake._unwrap_data(raw_result)
                fundamentals = data.get("fundementals", []) if isinstance(data, dict) else []
                extracted: dict[str, float | None] = {}
                for item in fundamentals:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "")).lower()
                    values = item.get("values", [])
                    ttm = values[0] if values else None
                    if "price earnings" in name or "p/e" in name:
                        extracted["pe"] = float(ttm) if ttm is not None else None
                    elif "earnings per share" in name:
                        extracted["eps"] = float(ttm) if ttm is not None else None
                    elif "book value per share" in name:
                        extracted["book_value"] = float(ttm) if ttm is not None else None
                    elif "dividend yield" in name:
                        extracted["div_yield"] = float(ttm) if ttm is not None else None
                    elif "net profit margin" in name:
                        extracted["net_margin"] = float(ttm) if ttm is not None else None
                    elif "price/book" in name or "price to book" in name:
                        extracted["pb"] = float(ttm) if ttm is not None else None
                return extracted

            ticker_metrics = {t: extract_metrics(r) for t, r in zip(all_tickers, results)}
            subject_metrics = ticker_metrics.get(upper, {})
            peer_data = [ticker_metrics[t] for t in peer_tickers if t in ticker_metrics]

            def peer_avg(key: str) -> float | None:
                vals = [m[key] for m in peer_data if m.get(key) is not None]
                return sum(vals) / len(vals) if vals else None

            def sector_avg(key: str) -> float | None:
                all_vals = [m[key] for m in ticker_metrics.values() if m.get(key) is not None]
                return sum(all_vals) / len(all_vals) if all_vals else None

            def fmt(val: float | None, pct: bool = False) -> str:
                if val is None:
                    return "—"
                if pct:
                    return f"{val:.1f}%"
                return f"{val:.2f}"

            def positions(subj: float | None, peers_val: float | None, sect_val: float | None) -> dict[str, int]:
                vals = [v for v in [subj, peers_val, sect_val] if v is not None]
                if not vals:
                    return {"subject": 50, "peers": 50, "sector": 50}
                lo, hi = min(vals), max(vals)
                span = hi - lo or 1

                def pct_pos(v: float | None) -> int:
                    return int((v - lo) / span * 90 + 5) if v is not None else 50

                return {
                    "subject": pct_pos(subj),
                    "peers": pct_pos(peers_val),
                    "sector": pct_pos(sect_val),
                }

            rows: list[PeerMetric] = []
            metric_defs = [
                ("P/E Ratio", "pe", False),
                ("EPS (Rs.)", "eps", False),
                ("Book Value/Share", "book_value", False),
                ("Dividend Yield", "div_yield", True),
                ("Net Profit Margin", "net_margin", True),
            ]
            for label, key, is_pct in metric_defs:
                s = subject_metrics.get(key)
                p = peer_avg(key)
                se = sector_avg(key)
                pos = positions(s, p, se)
                rows.append(
                    PeerMetric(
                        metric=label,
                        subject=fmt(s, is_pct),
                        peers=fmt(p, is_pct),
                        sector=fmt(se, is_pct),
                        positions=PeerMetricPositions(**pos),
                    )
                )

            return PeersComparisonResponse(
                ticker=upper,
                sector=sector_code,
                peers=peer_tickers,
                categories=["Value"],
                metrics=rows,
            )

        return await self._cached(cache_key, PEERS_CACHE_TTL, fetch)

    async def get_related(self, ticker: str, limit: int = 5) -> tuple[RelatedTickersResponse, bool, int]:
        cache_key = f"market:related:{ticker.upper()}:{limit}"

        async def fetch():
            profile = self.capital_stake._unwrap_data(
                await self.capital_stake.get_company_profile_basic(ticker)
            )
            sector = str(profile.get("sector", profile.get("sector_code", "0801")))
            items: list[dict[str, Any]] = []
            try:
                constituents = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_sector_constituents(sector)
                )
                if isinstance(constituents, list):
                    for c in constituents[: limit + 1]:
                        if not isinstance(c, dict):
                            continue
                        sym = str(c.get("ticker", c.get("symbol", c.get("s", "")))).upper()
                        if sym and sym != ticker.upper():
                            try:
                                q = await self.capital_stake.get_stock_quote(sym)
                                items.append({
                                    "ticker": sym,
                                    "name": q.name,
                                    "price": q.price,
                                    "change_percent": q.change_percent,
                                })
                            except ExternalServiceError:
                                items.append({"ticker": sym, "name": sym, "price": 0, "change_percent": 0})
                        if len(items) >= limit:
                            break
            except ExternalServiceError:
                pass
            return map_related(ticker, items)

        return await self._cached(cache_key, RELATED_CACHE_TTL, fetch)

    async def get_opex_dates(self, ticker: str) -> tuple[OpexDatesResponse, bool, int]:
        cache_key = f"market:opex:{ticker.upper()}"

        async def fetch():
            return compute_opex_dates(ticker)

        return await self._cached(cache_key, OPEX_CACHE_TTL, fetch)

    async def get_market_summary(self) -> tuple[MarketSummaryResponse, bool, int]:
        cache_key = "market:summary"

        async def fetch():
            indices_resp, kse100_resp, status_resp = await asyncio.gather(
                self.capital_stake.get_indices(),
                self.capital_stake.get_index("KSE100"),
                self.capital_stake.get_market_status(),
                return_exceptions=True,
            )

            indices_raw = (
                self.capital_stake._unwrap_data(indices_resp)
                if not isinstance(indices_resp, Exception)
                else []
            )
            indices_list = indices_raw if isinstance(indices_raw, list) else _rows_from_list(indices_raw)

            kse100_data: dict[str, Any] = {}
            if not isinstance(kse100_resp, Exception):
                unwrapped = self.capital_stake._unwrap_data(kse100_resp)
                if isinstance(unwrapped, dict):
                    kse100_data = unwrapped

            market_status = "Closed"
            if not isinstance(status_resp, Exception):
                status_raw = self.capital_stake._unwrap_data(status_resp)
                if isinstance(status_raw, dict):
                    market_status = _map_v3_market_state(
                        str(
                            status_raw.get("state")
                            or status_raw.get("status")
                            or status_raw.get("marketStatus")
                            or status_raw.get("market_status")
                            or "SUS"
                        )
                    )

            featured_symbol = "KSE100"
            for row in indices_list:
                if not isinstance(row, dict):
                    continue
                symbol = str(
                    row.get("symbol")
                    or row.get("ticker")
                    or row.get("code")
                    or row.get("s")
                    or ""
                ).upper()
                normalized = symbol.replace("-", "").replace("_", "")
                if normalized == "KSE100" or "KSE100" in normalized:
                    featured_symbol = symbol or "KSE100"
                    break

            chart_points = []
            try:
                eod_raw = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_eod_data(featured_symbol, lookback_days=35)
                )
                chart_points = map_ohlcv(featured_symbol, eod_raw, "1mo", "1d").points
            except ExternalServiceError:
                chart_points = []

            return map_market_summary(
                indices_list,
                chart_points,
                market_status=market_status,
                kse100_override=kse100_data or None,
            )

        return await self._cached(cache_key, SUMMARY_CACHE_TTL, fetch)

    async def stream_quote(self, ticker: str) -> AsyncIterator[str]:
        """M6 — SSE quote stream with heartbeat."""
        heartbeat_interval = 15
        poll_interval = 10
        elapsed = 0
        try:
            while True:
                try:
                    quote, _, _ = await self.get_quote(ticker)
                    payload = {
                        "ticker": quote.ticker,
                        "price": quote.price,
                        "change": quote.change,
                        "change_percent": quote.change_percent,
                        "volume": 0,
                        "timestamp": int(asyncio.get_event_loop().time() * 1000),
                    }
                    yield f"event: quote_update\ndata: {json.dumps(payload)}\n\n"
                    if quote.status == "Closed":
                        yield f"event: market_closed\ndata: {json.dumps({'ticker': ticker, 'close_price': quote.price})}\n\n"
                except ExternalServiceError as exc:
                    yield f"event: error\ndata: {json.dumps({'code': exc.error_code, 'message': exc.message, 'retry': True})}\n\n"

                for _ in range(poll_interval):
                    await asyncio.sleep(1)
                    elapsed += 1
                    if elapsed >= heartbeat_interval:
                        yield ": ping\n\n"
                        elapsed = 0
        except asyncio.CancelledError:
            yield f"event: stream_end\ndata: {json.dumps({'reason': 'client_disconnect'})}\n\n"

    async def get_all_prices(self) -> list[Price]:
        if not self.settings.psx_proxy_base_url:
            raise ExternalServiceError("PSX Proxy", "URL not configured", error_code="PSX_PROXY_NOT_CONFIGURED")
        return await self.psx_client.get_all_prices()

    async def get_price(self, ticker: str) -> Price:
        if not self.settings.psx_proxy_base_url:
            raise ExternalServiceError("PSX Proxy", "URL not configured", error_code="PSX_PROXY_NOT_CONFIGURED")
        return await self.psx_client.get_price(ticker)
