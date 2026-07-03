from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class RerankResult:
    index: int
    score: float
    text: str


class Reranker(Protocol):
    async def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int | None = None,
    ) -> list[RerankResult]: ...
