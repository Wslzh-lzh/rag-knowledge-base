from __future__ import annotations

import logging

from app.core.config import settings
from app.services.rerankers.base import Reranker
from app.services.rerankers.dashscope_reranker import DashScopeReranker
from app.services.rerankers.mock_reranker import MockReranker

logger = logging.getLogger(__name__)

_reranker: Reranker | None = None


def get_reranker(provider: str | None = None) -> Reranker:
    global _reranker
    if _reranker is None:
        _provider = provider or settings.default_reranker_provider
        if _provider == "dashscope":
            try:
                _reranker = DashScopeReranker()
                logger.info("Using DashScope reranker: %s", settings.dashscope_reranker_model)
            except Exception as e:
                logger.warning("DashScope reranker init failed, falling back to mock: %s", e)
                _reranker = MockReranker()
        else:
            _reranker = MockReranker()
            logger.info("Using mock reranker")
    return _reranker
