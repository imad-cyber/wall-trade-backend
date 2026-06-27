"""Validate parsed analysis results."""
from app.domain.analysis.models import AnalysisResult


class AnalysisValidator:
    def validate(self, result: AnalysisResult) -> AnalysisResult:
        if not result.ticker:
            raise ValueError("ticker is required")
        if not result.verdict:
            raise ValueError("verdict is required")
        if not result.summary:
            raise ValueError("summary is required")
        return result
