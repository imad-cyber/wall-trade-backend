"""Parse raw AI text into AnalysisResult domain model."""
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.config import get_settings
from app.domain.analysis.enums import Sentiment
from app.domain.analysis.models import AnalysisResult


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


class AnalysisParser:
    def parse(self, raw_text: str, ticker: str) -> AnalysisResult:
        data = self._extract_json(raw_text)
        settings = get_settings()
        now = datetime.now(timezone.utc)
        try:
            sentiment = Sentiment(data.get("sentiment", "neutral"))
        except ValueError:
            sentiment = Sentiment.NEUTRAL
        return AnalysisResult(
            ticker=ticker.upper(),
            summary=data.get("summary", "Analysis completed."),
            sentiment=sentiment,
            verdict=data.get("verdict", "HOLD"),
            key_risks=data.get("risks") or data.get("key_risks") or [],
            key_opportunities=data.get("key_opportunities") or [],
            analysis=data.get("analysis") or [],
            key_factors=data.get("key_factors") or [],
            generated_at=now,
            expires_at=now + timedelta(hours=settings.ANALYSIS_CACHE_TTL_HOURS),
            model_used=settings.AI_MODEL,
        )

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "verdict": "HOLD",
            "summary": text[:500] if text else "Unable to parse AI response.",
            "sentiment": "neutral",
            "analysis": [text[:200]] if text else [],
            "risks": [],
            "key_opportunities": [],
        }
