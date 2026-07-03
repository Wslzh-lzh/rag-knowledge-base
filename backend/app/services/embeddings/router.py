from __future__ import annotations

from app.core.config import settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.dashscope_provider import DashScopeEmbeddingProvider
from app.services.embeddings.mock_provider import MockEmbeddingProvider


def get_embedding_provider(provider: str | None = None) -> EmbeddingProvider:
    _provider = provider or settings.default_embedding_provider

    if _provider == "dashscope":
        return DashScopeEmbeddingProvider()

    if _provider == "mock":
        return MockEmbeddingProvider(dim=settings.embedding_dim)

    return MockEmbeddingProvider(dim=settings.embedding_dim)
