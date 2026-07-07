from __future__ import annotations

import asyncio

from app.core.config import settings
from app.services.embeddings.dashscope_provider import DashScopeEmbeddingProvider
from app.services.llm.base import LLMMessage
from app.services.llm.router import get_llm_client
from app.services.rerankers.dashscope_reranker import DashScopeReranker


async def main() -> None:
    print("DashScope readiness")
    print(f"- api key present: {settings.can_use_dashscope()}")
    print(f"- llm provider: {settings.default_llm_provider}")
    print(f"- embedding provider: {settings.default_embedding_provider}")
    print(f"- reranker provider: {settings.default_reranker_provider}")

    if not settings.can_use_dashscope():
        raise SystemExit("DASHSCOPE_API_KEY is missing")

    embedding_provider = DashScopeEmbeddingProvider()
    embedding = await embedding_provider.embed("你好，帮我做一个联通性检查。")
    print(f"- embedding ok: dim={len(embedding.embedding)}")

    reranker = DashScopeReranker()
    rerank_results = await reranker.rerank(
        "什么是装饰器",
        ["装饰器用于包装函数。", "列表可以追加元素。"],
        top_n=1,
    )
    print(f"- reranker ok: top_score={rerank_results[0].score if rerank_results else 'n/a'}")

    llm = get_llm_client("dashscope")
    llm_result = await llm.generate(
        [LLMMessage(role="user", content="请只回复：DashScope 正常")],
        temperature=0,
    )
    print(f"- llm ok: {llm_result.content}")


if __name__ == "__main__":
    asyncio.run(main())
