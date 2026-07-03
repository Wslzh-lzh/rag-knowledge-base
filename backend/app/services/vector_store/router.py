from __future__ import annotations

import logging

from app.core.config import settings
from app.services.vector_store.base import VectorStore
from app.services.vector_store.memory_store import InMemoryVectorStore
from app.services.vector_store.qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)

_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        backend = settings.vector_store_backend
        if backend == "qdrant":
            try:
                _vector_store = QdrantVectorStore()
                logger.info("Using Qdrant vector store: %s", settings.qdrant_url)
            except Exception as e:
                logger.warning("Qdrant connection failed, falling back to memory store: %s", e)
                _vector_store = InMemoryVectorStore()
        else:
            _vector_store = InMemoryVectorStore()
            logger.info("Using in-memory vector store")
    return _vector_store
