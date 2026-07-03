from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class VectorSearchHit:
    chunk_id: str
    document_id: str
    document_name: str
    kb_id: str
    score: float
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict | None = None


class VectorStore(Protocol):
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
    ) -> None: ...

    async def search(
        self,
        collection_name: str,
        *,
        query_embedding: list[float],
        top_k: int = 10,
        kb_ids: list[str] | None = None,
    ) -> list[VectorSearchHit]: ...

    async def delete_by_chunk_id(self, collection_name: str, chunk_id: str) -> None: ...

    async def delete_by_document_id(self, collection_name: str, document_id: str) -> None: ...

    async def ensure_collection(self, collection_name: str, dim: int) -> None: ...
