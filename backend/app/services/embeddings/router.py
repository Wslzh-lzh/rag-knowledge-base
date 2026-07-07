from __future__ import annotations

import logging

from app.core.config import settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.dashscope_provider import DashScopeEmbeddingProvider
from app.services.embeddings.mock_provider import MockEmbeddingProvider

logger = logging.getLogger(__name__)


def get_embedding_provider(provider: str | None = None) -> EmbeddingProvider:
    _provider = provider or settings.default_embedding_provider

    if _provider == "dashscope":
        if not settings.can_use_dashscope():
            logger.warning("DashScope embedding provider requested but DASHSCOPE_API_KEY is missing, falling back to mock")
            return MockEmbeddingProvider(dim=settings.embedding_dim)
        return DashScopeEmbeddingProvider()

    if _provider == "mock":
        return MockEmbeddingProvider(dim=settings.embedding_dim)

    return MockEmbeddingProvider(dim=settings.embedding_dim)
