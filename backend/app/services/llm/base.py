from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResult:
    content: str
    usage: dict
    raw: dict | None = None


class LLMClient(Protocol):
    async def generate(self, messages: list[LLMMessage], *, temperature: float = 0.2, stream: bool = False) -> LLMResult: ...

