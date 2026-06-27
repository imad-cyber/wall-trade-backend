"""AI provider protocol and schemas."""
from typing import AsyncIterator, Protocol


class AIProvider(Protocol):
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...

    async def complete(self, prompt: str) -> str: ...
