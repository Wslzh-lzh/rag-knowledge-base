from __future__ import annotations

from app.core.config import settings
from app.services.embeddings.base import EmbeddingResult


class DashScopeEmbeddingProvider:
    """DashScope Embedding Provider（OpenAI 兼容模式）。

    支持阿里云灵积的 text-embedding-v1/v2/v3 等 Embedding 模型。
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        dim: int | None = None,
    ):
        self.api_key = api_key or settings.dashscope_api_key
        self.base_url = (base_url or settings.dashscope_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
        self.model = model or settings.dashscope_embedding_model
        self.dim = dim or settings.embedding_dim

    async def embed(self, text: str) -> EmbeddingResult:
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        max_batch_size = 10
        all_results: list[EmbeddingResult] = []
        total_usage = {}

        for i in range(0, len(texts), max_batch_size):
            batch = texts[i:i + max_batch_size]
            body = {
                "model": self.model,
                "input": batch,
            }

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{self.base_url}/embeddings", headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

            usage = data.get("usage", {})
            for k, v in usage.items():
                total_usage[k] = total_usage.get(k, 0) + v

            for item in data["data"]:
                all_results.append(
                    EmbeddingResult(
                        embedding=item["embedding"],
                        model=self.model,
                        usage=usage,
                    )
                )

        for result in all_results:
            result.usage = total_usage

        return all_results
