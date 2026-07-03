from __future__ import annotations

import math
from dataclasses import dataclass, field

from .base import VectorSearchHit


@dataclass
class _VectorItem:
    chunk_id: str
    embedding: list[float]
    document_id: str
    document_name: str
    kb_id: str
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict = field(default_factory=dict)


class InMemoryVectorStore:
    """In-memory vector store for local development.

    Uses cosine similarity search. Not suitable for production.
    """

    def __init__(self):
        self._collections: dict[str, dict[str, _VectorItem]] = {}

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "backend": "memory",
            "collections_count": len(self._collections),
        }

    async def ensure_collection(self, collection_name: str, dim: int) -> None:
        if collection_name not in self._collections:
            self._collections[collection_name] = {}

    async def upsert(
        self,
        collection_name: str,
        *,
        chunk_id: str,
        embedding: list[float],
        document_id: str,
        document_name: str,
        kb_id: str,
        page_start: int | None = None,
        page_end: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self.ensure_collection(collection_name, len(embedding))
        self._collections[collection_name][chunk_id] = _VectorItem(
            chunk_id=chunk_id,
            embedding=embedding,
            document_id=document_id,
            document_name=document_name,
            kb_id=kb_id,
            page_start=page_start,
            page_end=page_end,
            metadata=metadata or {},
        )

    async def search(
        self,
        collection_name: str,
        *,
        query_embedding: list[float],
        top_k: int = 10,
        kb_ids: list[str] | None = None,
    ) -> list[VectorSearchHit]:
        if collection_name not in self._collections:
            return []

        items = list(self._collections[collection_name].values())
        if kb_ids:
            items = [item for item in items if item.kb_id in kb_ids]

        scored = []
        for item in items:
            score = self._cosine_similarity(query_embedding, item.embedding)
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_items = scored[:top_k]

        return [
            VectorSearchHit(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                document_name=item.document_name,
                kb_id=item.kb_id,
                score=score,
                page_start=item.page_start,
                page_end=item.page_end,
                metadata=item.metadata,
            )
            for score, item in top_items
        ]

    async def delete_by_chunk_id(self, collection_name: str, chunk_id: str) -> None:
        if collection_name in self._collections:
            self._collections[collection_name].pop(chunk_id, None)

    async def delete_by_document_id(self, collection_name: str, document_id: str) -> None:
        if collection_name not in self._collections:
            return
        to_delete = [
            cid for cid, item in self._collections[collection_name].items()
            if item.document_id == document_id
        ]
        for cid in to_delete:
            del self._collections[collection_name][cid]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
