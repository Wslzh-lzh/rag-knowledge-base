from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class FulltextSearchHit:
    chunk_id: str
    document_id: str
    document_name: str
    kb_id: str
    score: float
    page_start: int | None = None
    page_end: int | None = None
    content: str = ""
    highlight: str | None = None
    metadata: dict | None = field(default=None)


class FulltextSearcher(Protocol):
    async def index_chunk(
        self,
        *,
        chunk_id: str,
        document_id: str,
        document_name: str,
        kb_id: str,
        content: str,
        page_start: int | None = None,
        page_end: int | None = None,
        metadata: dict | None = None,
    ) -> None: ...

    async def search(
        self,
        query: str,
        *,
        kb_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FulltextSearchHit]: ...

    async def delete_by_chunk_id(self, chunk_id: str) -> None: ...

    async def delete_by_document_id(self, document_id: str) -> None: ...
