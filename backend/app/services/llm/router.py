from __future__ import annotations

from app.core.config import settings
from app.services.llm.base import LLMClient
from app.services.llm.openai_client import OpenAICompatibleClient


class EchoLLMClient:
    async def generate(self, messages, *, temperature: float = 0.2, stream: bool = False):
        from app.services.llm.base import LLMResult

        prompt = messages[-1].content if messages else ""
        return LLMResult(
            content=f"[Echo LLM] 你说的是：{prompt}",
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(prompt) // 2, "total_tokens": len(prompt)},
            raw={"provider": "echo"},
        )


def get_llm_client(provider: str | None = None) -> LLMClient:
    _provider = provider or settings.default_llm_provider

    if _provider == "dashscope":
        return OpenAICompatibleClient(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            model=settings.dashscope_llm_model,
        )

    if _provider == "openai":
        return OpenAICompatibleClient()

    return EchoLLMClient()
