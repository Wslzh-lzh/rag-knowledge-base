from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class EmbeddingResult:
    embedding: list[float]
    model: str
    usage: dict | None = None


class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> EmbeddingResult: ...

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]: ...
