from __future__ import annotations

import hashlib
import math

from .base import EmbeddingResult


class MockEmbeddingProvider:
    """Mock embedding provider for local development.

    Generates deterministic pseudo-embeddings based on text hash.
    Not suitable for production use.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.model = "mock-embedding"

    async def embed(self, text: str) -> EmbeddingResult:
        embedding = self._text_to_embedding(text)
        return EmbeddingResult(
            embedding=embedding,
            model=self.model,
            usage={"prompt_tokens": len(text.split())},
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed(text) for text in texts]

    def _text_to_embedding(self, text: str) -> list[float]:
        """Generate a deterministic pseudo-embedding from text.

        Uses multiple hash rounds to produce a normalized vector.
        This is NOT a real embedding - it's just for testing.
        """
        vector = [0.0] * self.dim
        text_bytes = text.encode("utf-8")

        for i in range(self.dim):
            h = hashlib.sha256(text_bytes + str(i).encode()).digest()
            val = int.from_bytes(h[:4], "big", signed=True) / 2**31
            vector[i] = val

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector
