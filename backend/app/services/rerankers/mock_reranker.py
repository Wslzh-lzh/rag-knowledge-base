from __future__ import annotations

from .base import RerankResult


class MockReranker:
    """Mock Reranker，直接返回原始分数（不做重排）。

    用于本地开发，保持接口兼容但不进行实际重排。
    """

    def __init__(self):
        self.model = "mock-reranker"

    async def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int | None = None,
    ) -> list[RerankResult]:
        results = [
            RerankResult(
                index=i,
                score=1.0 / (i + 1),
                text=doc,
            )
            for i, doc in enumerate(documents)
        ]
        if top_n is not None:
            results = results[:top_n]
        return results
