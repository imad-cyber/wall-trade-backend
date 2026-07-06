"""AI analysis service — AI1, AI2, AI3."""
import uuid
from typing import Any, AsyncIterator, Optional

from app.ai.analysis_pipeline import AnalysisPipeline
from app.api.v1.schemas.ai import AIAnalyzeRequest, AIAnalyzeResponse, AIReportResponse
from app.core.config import get_settings
from app.repositories.analysis_repository import AnalysisRepository
from app.services.cache_service import CacheService


class AIService:
    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        cache_service: CacheService,
        pipeline: Optional[AnalysisPipeline] = None,
    ):
        self.analysis_repo = analysis_repo
        self.cache_service = cache_service
        self.pipeline = pipeline
        self.settings = get_settings()

    def trigger_analysis(self, ticker: str, request: AIAnalyzeRequest) -> AIAnalyzeResponse:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        return AIAnalyzeResponse(
            job_id=job_id,
            ticker=ticker.upper(),
            status="queued",
            stream_url=f"/api/v1/ai/stream/{ticker.upper()}?job_id={job_id}",
        )

    def get_last_report(self, ticker: str) -> AIReportResponse:
        cached = self.cache_service.get_analysis(ticker)
        if cached:
            return AIReportResponse(
                ticker=ticker.upper(),
                analysis=cached.model_dump(mode="json") if hasattr(cached, "model_dump") else dict(cached),
                generated_at=getattr(cached, "generated_at", None),
            )
        return AIReportResponse(ticker=ticker.upper(), analysis={})

    async def stream_analysis(self, ticker: str, job_id: str | None = None) -> AsyncIterator[str]:
        if self.pipeline is None:
            yield "event: analysis_error\ndata: {\"message\": \"Pipeline not configured\"}\n\n"
            return
        async for event in self.pipeline.run(ticker, refresh=True):
            yield event
        yield "event: analysis_complete\ndata: {\"status\": \"done\"}\n\n"
