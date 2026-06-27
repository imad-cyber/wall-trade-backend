"""OpenAI client implementing AIProvider protocol."""
import json
from typing import AsyncIterator, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.observability.metrics import record_ai_latency
import time

logger = get_logger(__name__)


class OpenAIClient:
    """Streams completions from OpenAI Chat Completions API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self._base_url = "https://api.openai.com/v1"

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        if not self.api_key:
            yield "AI provider is not configured."
            return

        start = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=body,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        record_ai_latency(self.model, (time.perf_counter() - start) * 1000)

    async def complete(self, prompt: str) -> str:
        parts = []
        async for token in self.stream(prompt):
            parts.append(token)
        return "".join(parts)


class MockAIProvider:
    """Mock AI provider for tests and offline development."""

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        yield '{"verdict": "HOLD", "summary": "Mock analysis", '
        yield '"sentiment": "neutral", "analysis": ["Mock point"], '
        yield '"risks": ["Market risk"], "key_opportunities": ["Growth"]}'

    async def complete(self, prompt: str) -> str:
        return (
            '{"verdict": "HOLD", "summary": "Mock analysis", '
            '"sentiment": "neutral", "analysis": ["Mock point"], '
            '"risks": ["Market risk"], "key_opportunities": ["Growth"]}'
        )
