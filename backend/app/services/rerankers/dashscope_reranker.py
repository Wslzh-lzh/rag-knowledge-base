from __future__ import annotations

from app.core.config import settings
from app.services.rerankers.base import RerankResult


class DashScopeReranker:
    """DashScope Reranker（阿里云百炼文本排序 API）。

    支持 gte-rerank-v2 / qwen3-rerank 等重排模型。
    API 端点: https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.dashscope_api_key
        self.base_url = (
            base_url
            or "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
        )
        self.model = model or settings.dashscope_reranker_model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int | None = None,
    ) -> list[RerankResult]:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        body = {
            "model": self.model,
            "input": {
                "query": query,
                "documents": documents,
            },
        }
        if top_n is not None:
            body["parameters"] = {"top_n": top_n}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.base_url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        results: list[RerankResult] = []
        output = data.get("output", {})
        for item in output.get("results", []):
            idx = item.get("index", 0)
            results.append(
                RerankResult(
                    index=idx,
                    score=item.get("relevance_score", 0.0),
                    text=documents[idx] if 0 <= idx < len(documents) else "",
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results

