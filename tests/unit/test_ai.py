"""AI module unit tests."""
import json

from app.ai.parser import AnalysisParser
from app.ai.prompt_builder import PromptBuilder
from app.ai.streaming import StreamManager
from app.ai.validator import AnalysisValidator
from app.domain.analysis.enums import Sentiment


class TestPromptBuilder:
    def test_prompt_builder_builds_structured_prompt(self):
        builder = PromptBuilder()
        prompt = builder.build("ENGRO", {"revenue": 1000}, None)
        assert "ENGRO" in prompt
        assert "revenue" in prompt


class TestStreamManager:
    def test_stream_manager_formats_sse(self):
        event = StreamManager.format_sse("hello")
        assert event.startswith("event: message")
        assert "hello" in event

    def test_done_event(self):
        assert StreamManager.done_event() == "data: [DONE]\n\n"


class TestAnalysisParser:
    def test_analysis_parser_extracts_verdict(self):
        raw = json.dumps({
            "verdict": "BUY",
            "summary": "Good stock",
            "sentiment": "bullish",
            "analysis": ["Point 1"],
            "risks": [],
        })
        result = AnalysisParser().parse(raw, "ENGRO")
        assert result.verdict == "BUY"
        assert result.sentiment == Sentiment.BULLISH


class TestAnalysisValidator:
    def test_analysis_validator_rejects_invalid(self):
        from datetime import datetime, timezone
        from app.domain.analysis.models import AnalysisResult

        validator = AnalysisValidator()
        valid = AnalysisResult(
            ticker="ENGRO",
            summary="test",
            verdict="HOLD",
            generated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
        )
        assert validator.validate(valid).ticker == "ENGRO"
