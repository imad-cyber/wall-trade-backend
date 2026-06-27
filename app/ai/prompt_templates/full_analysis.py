"""Jinja2/f-string analysis prompt templates."""
FULL_ANALYSIS_TEMPLATE = """You are a financial analyst for the Pakistan Stock Exchange (PSX).

Analyze the following stock: {ticker}

Company Financial Data:
{company_data}

Macro Economic Context:
{macro_data}

Provide a structured JSON response with these fields:
- verdict: BUY, HOLD, or SELL
- summary: 2-3 sentence executive summary
- sentiment: bullish, bearish, or neutral
- analysis: list of 3-5 key analytical points
- key_factors: list of important factors
- risks: list of key risks
- key_opportunities: list of opportunities
"""

QUICK_SUMMARY_TEMPLATE = """Provide a brief market summary for {ticker} based on:
{macro_data}
"""
