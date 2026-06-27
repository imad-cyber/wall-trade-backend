"""Analysis domain models."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.analysis.enums import ConfidenceLevel, Sentiment


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.utcnow()


class AnalysisResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    summary: str
    sentiment: Sentiment = Sentiment.NEUTRAL
    verdict: str
    key_risks: list[str] = Field(default_factory=list)
    key_opportunities: list[str] = Field(default_factory=list)
    analysis: list[str] = Field(default_factory=list)
    key_factors: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    generated_at: datetime
    expires_at: datetime
    model_used: str = "gpt-4o"

    @classmethod
    def from_db_analysis(cls, ticker: str, raw: dict[str, Any], row: dict[str, Any]) -> "AnalysisResult":
        analysis_data = raw if isinstance(raw, dict) else {}
        sentiment_raw = analysis_data.get("sentiment", "neutral")
        try:
            sentiment = Sentiment(sentiment_raw)
        except ValueError:
            sentiment = Sentiment.NEUTRAL
        generated = row.get("generated_at")
        expires = row.get("expires_at")
        return cls(
            ticker=ticker.upper(),
            summary=analysis_data.get("summary") or row.get("summary", ""),
            sentiment=sentiment,
            verdict=analysis_data.get("verdict") or row.get("verdict", ""),
            key_risks=analysis_data.get("risks") or analysis_data.get("key_risks") or [],
            key_opportunities=analysis_data.get("key_opportunities") or [],
            analysis=analysis_data.get("analysis") or [],
            key_factors=analysis_data.get("key_factors") or [],
            generated_at=_parse_dt(generated) if generated else datetime.now(timezone.utc),
            expires_at=_parse_dt(expires) if expires else datetime.now(timezone.utc),
            model_used=row.get("model_used", "gpt-4o"),
        )


class AnalysisCache(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: Optional[int] = None
    ticker: str
    result: AnalysisResult
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "AnalysisCache":
        ticker = row.get("ticker", "")
        analysis_raw = row.get("analysis") or {}
        result = AnalysisResult.from_db_analysis(ticker, analysis_raw, row)
        return cls(
            id=row.get("id"),
            ticker=ticker.upper(),
            result=result,
            created_at=row.get("generated_at") or row.get("created_at"),
        )

    def to_db_payload(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker.upper(),
            "verdict": self.result.verdict,
            "summary": self.result.summary,
            "analysis": {
                "verdict": self.result.verdict,
                "summary": self.result.summary,
                "analysis": self.result.analysis,
                "key_factors": self.result.key_factors,
                "risks": self.result.key_risks,
                "sentiment": self.result.sentiment.value,
                "key_opportunities": self.result.key_opportunities,
            },
            "generated_at": self.result.generated_at.isoformat(),
            "expires_at": self.result.expires_at.isoformat(),
            "model_used": self.result.model_used,
        }
