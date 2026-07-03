from __future__ import annotations

from typing import AsyncIterator

from app.core.config import settings
from app.services.llm.base import LLMClient, LLMMessage, LLMResult


class OpenAICompatibleClient:
    """OpenAI API 兼容的 LLM 客户端。

    支持任何 OpenAI 兼容的 API（如 OpenAI、DeepSeek、Moonshot、Qwen 等）。
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model or settings.default_llm_model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> LLMResult:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        body = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": stream,
        }

        if stream:
            raise NotImplementedError("Use generate_stream for streaming")

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        return LLMResult(
            content=choice["message"]["content"],
            usage=usage,
            raw=data,
        )

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        body = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue
