"""AI analysis pipeline orchestration."""
from typing import AsyncIterator, Optional

from app.ai.parser import AnalysisParser
from app.ai.prompt_builder import PromptBuilder
from app.ai.streaming import StreamManager
from app.ai.validator import AnalysisValidator
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.analysis.models import AnalysisCache
from app.observability.context import get_ctx
from app.observability.metrics import record_cache_hit
from app.providers.ai.openai_client import MockAIProvider, OpenAIClient
from app.providers.capital_stake.client import CapitalStakeClient
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.macro_repository import MacroRepository
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class AnalysisPipeline:
    def __init__(
        self,
        capital_stake: CapitalStakeClient,
        macro_repo: MacroRepository,
        analysis_repo: AnalysisRepository,
        cache_service: CacheService,
        prompt_builder: Optional[PromptBuilder] = None,
        ai_provider=None,
        parser: Optional[AnalysisParser] = None,
        validator: Optional[AnalysisValidator] = None,
    ):
        settings = get_settings()
        self.capital_stake = capital_stake
        self.macro_repo = macro_repo
        self.analysis_repo = analysis_repo
        self.cache_service = cache_service
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.ai_provider = ai_provider or (
            OpenAIClient() if settings.ai_api_key else MockAIProvider()
        )
        self.parser = parser or AnalysisParser()
        self.validator = validator or AnalysisValidator()
        self.stream_manager = StreamManager()

    async def run(self, ticker: str, *, refresh: bool = False) -> AsyncIterator[str]:
        ticker = ticker.upper()
        if not refresh:
            cached = self.cache_service.get_analysis(ticker)
            if cached:
                get_ctx().cache_hit = True
                record_cache_hit("analysis")
                yield self.stream_manager.cached_event(cached.model_dump(mode="json"))
                yield self.stream_manager.done_event()
                return

        yield self.stream_manager.status_event(f"Fetching data for {ticker}...")

        try:
            company_data = await self.capital_stake.get_financial_data(ticker)
        except Exception as exc:
            logger.warning("Capital Stake fetch failed: %s", exc)
            company_data = {"ticker": ticker}

        macro = self.macro_repo.get_latest()
        prompt = self.prompt_builder.build(ticker, company_data, macro)

        yield self.stream_manager.status_event("Generating analysis...")

        raw_parts: list[str] = []
        try:
            async for token in self.ai_provider.stream(prompt):
                raw_parts.append(token)
                yield self.stream_manager.format_sse(token)
        except Exception as exc:
            logger.error("AI streaming failed: %s", exc)
            yield self.stream_manager.error_event(str(exc))
            yield self.stream_manager.done_event()
            return

        raw_text = "".join(raw_parts)
        try:
            result = self.validator.validate(self.parser.parse(raw_text, ticker))
            cache = AnalysisCache(
                ticker=ticker,
                result=result,
            )
            saved = self.analysis_repo.upsert_cache(cache)
            yield self.stream_manager.status_event("Analysis saved to cache.")
            logger.info("Analysis cached for %s (id=%s)", ticker, saved.id)
        except Exception as exc:
            logger.warning("Failed to parse/save analysis: %s", exc)

        yield self.stream_manager.done_event()

    def get_cached(self, ticker: str) -> Optional[AnalysisCache]:
        return self.cache_service.get_analysis(ticker)
