"""Assembles structured prompts from domain models."""
import json
from typing import Any, Optional

from app.domain.macro.models import MacroCache
from app.ai.prompt_templates.full_analysis import FULL_ANALYSIS_TEMPLATE


class PromptBuilder:
    def build(
        self,
        ticker: str,
        company_data: dict[str, Any],
        macro_data: Optional[MacroCache] = None,
    ) -> str:
        macro_str = json.dumps(macro_data.raw_data if macro_data else {}, indent=2, default=str)
        company_str = json.dumps(company_data, indent=2, default=str)
        return FULL_ANALYSIS_TEMPLATE.format(
            ticker=ticker.upper(),
            company_data=company_str,
            macro_data=macro_str,
        )
