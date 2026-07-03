from __future__ import annotations

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.document import Document, DocumentChunk
from app.services.fulltext.base import FulltextSearchHit


class PostgreSQLFulltextSearcher:
    """基于 PostgreSQL 的全文检索实现。

    使用简单的关键词匹配（BM25-like），无需额外依赖。
    适合本地开发和小规模场景。
    """

    def __init__(self, session_factory=async_session_factory) -> None:
        self.session_factory = session_factory

    async def health_check(self) -> dict:
        try:
            async with self.session_factory() as db:
                from sqlalchemy import text

                result = await db.execute(text("SELECT 1"))
                result.scalar()
            return {"status": "healthy", "backend": "postgresql"}
        except Exception as e:
            return {"status": "unhealthy", "backend": "postgresql", "error": str(e)}

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
    ) -> None:
        pass

    async def search(
        self,
        query: str,
        *,
        kb_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FulltextSearchHit]:
        async with self.session_factory() as db:
            stmt = select(DocumentChunk, Document.file_name).join(
                Document, Document.id == DocumentChunk.document_id
            )
            if kb_ids:
                stmt = stmt.where(DocumentChunk.kb_id.in_(kb_ids))
            rows = (await db.execute(stmt)).all()

        scored: list[FulltextSearchHit] = []
        query_terms = [term for term in query.lower().split() if term]
        for chunk, document_name in rows:
            text = chunk.content.lower()
            score = 0.0
            highlight_terms = []
            for term in query_terms:
                count = float(text.count(term))
                score += count
                if count > 0:
                    highlight_terms.append(term)
            if score <= 0 and query_terms:
                continue

            highlight = self._build_highlight(chunk.content, highlight_terms) if highlight_terms else None

            scored.append(
                FulltextSearchHit(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=document_name,
                    kb_id=chunk.kb_id,
                    score=score if score > 0 else 0.01,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    content=chunk.content,
                    highlight=highlight,
                    metadata=chunk.metadata_,
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    async def delete_by_chunk_id(self, chunk_id: str) -> None:
        pass

    async def delete_by_document_id(self, document_id: str) -> None:
        pass

    @staticmethod
    def _build_highlight(content: str, terms: list[str], max_len: int = 200) -> str | None:
        lower = content.lower()
        first_pos = len(content)
        for term in terms:
            pos = lower.find(term.lower())
            if 0 <= pos < first_pos:
                first_pos = pos

        if first_pos >= len(content):
            return None

        start = max(0, first_pos - 30)
        end = min(len(content), start + max_len)
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        return snippet
