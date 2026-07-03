from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_factory
from app.models.document import Document, DocumentChunk
from app.schemas.search import SearchHit
from app.services.embeddings.router import get_embedding_provider
from app.services.fulltext.router import get_fulltext_searcher
from app.services.rerankers.router import get_reranker
from app.services.vector_store.router import get_vector_store


@dataclass
class RetrievalRequest:
    query: str
    knowledge_base_ids: list[str] = field(default_factory=list)
    top_k: int = 10
    metadata_filter: dict = field(default_factory=dict)
    use_vector_search: bool = True
    use_bm25: bool = True
    use_reranker: bool = True
    hybrid_mode: str = "rrf"  # rrf / weighted


class HybridRetriever:
    def __init__(self, session_factory=async_session_factory) -> None:
        self.session_factory = session_factory
        self._embedding = get_embedding_provider()
        self._vector_store = get_vector_store()
        self._fulltext = get_fulltext_searcher()
        self._reranker = get_reranker() if settings.default_reranker_provider != "mock" else None

    async def retrieve(self, request: RetrievalRequest) -> list[SearchHit]:
        bm25_hits: list[SearchHit] = []
        vector_hits: list[SearchHit] = []

        if request.use_bm25:
            bm25_hits = await self._bm25_search(request)

        if request.use_vector_search:
            vector_hits = await self._vector_search(request)

        if request.use_bm25 and request.use_vector_search:
            merged = self._rrf_merge(bm25_hits, vector_hits, request.top_k * 2)
        elif request.use_vector_search:
            merged = vector_hits[: request.top_k * 2]
        else:
            merged = bm25_hits[: request.top_k * 2]

        if request.use_reranker and self._reranker and merged:
            merged = await self._rerank(request.query, merged, request.top_k)

        return merged[: request.top_k]

    async def _rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]:
        try:
            texts = [hit.content for hit in hits]
            results = await self._reranker.rerank(query, texts, top_n=top_k)
            reranked = []
            for r in results:
                if 0 <= r.index < len(hits):
                    hit = hits[r.index]
                    new_source = f"{hit.source_type}_reranked" if "reranked" not in hit.source_type else hit.source_type
                    reranked.append(
                        SearchHit(
                            **{
                                **hit.model_dump(),
                                "similarity_score": r.score,
                                "source_type": new_source,
                            }
                        )
                    )
            return reranked
        except Exception:
            return hits[:top_k]

    async def _bm25_search(self, request: RetrievalRequest) -> list[SearchHit]:
        try:
            ft_hits = await self._fulltext.search(
                request.query,
                kb_ids=request.knowledge_base_ids or None,
                top_k=request.top_k * 2,
            )

            hits: list[SearchHit] = []
            async with self.session_factory() as db:
                for fhit in ft_hits:
                    stmt = select(DocumentChunk, Document.file_name).join(
                        Document, Document.id == DocumentChunk.document_id
                    ).where(DocumentChunk.id == fhit.chunk_id)
                    row = (await db.execute(stmt)).first()
                    if not row:
                        continue
                    chunk, document_name = row
                    hits.append(
                        SearchHit(
                            chunk_id=chunk.id,
                            document_id=chunk.document_id,
                            document_name=document_name,
                            kb_id=chunk.kb_id,
                            page_start=fhit.page_start or chunk.page_start,
                            page_end=fhit.page_end or chunk.page_end,
                            content=chunk.content,
                            similarity_score=fhit.score,
                            source_type="bm25",
                            highlight=fhit.highlight,
                            metadata=chunk.metadata_,
                        )
                    )
            return hits
        except Exception:
            return []

    async def _vector_search(self, request: RetrievalRequest) -> list[SearchHit]:
        try:
            embedding_result = await self._embedding.embed(request.query)
            vector_hits = await self._vector_store.search(
                settings.qdrant_collection,
                query_embedding=embedding_result.embedding,
                top_k=request.top_k * 2,
                kb_ids=request.knowledge_base_ids or None,
            )

            hits: list[SearchHit] = []
            async with self.session_factory() as db:
                for vhit in vector_hits:
                    stmt = select(DocumentChunk, Document.file_name).join(
                        Document, Document.id == DocumentChunk.document_id
                    ).where(DocumentChunk.id == vhit.chunk_id)
                    row = (await db.execute(stmt)).first()
                    if not row:
                        continue
                    chunk, document_name = row
                    hits.append(
                        SearchHit(
                            chunk_id=chunk.id,
                            document_id=chunk.document_id,
                            document_name=document_name,
                            kb_id=chunk.kb_id,
                            page_start=chunk.page_start,
                            page_end=chunk.page_end,
                            content=chunk.content,
                            similarity_score=vhit.score,
                            source_type="vector",
                            metadata=chunk.metadata_,
                        )
                    )
            return hits
        except Exception:
            return []

    @staticmethod
    def _rrf_merge(
        bm25_hits: list[SearchHit],
        vector_hits: list[SearchHit],
        top_k: int,
        k: int = 60,
    ) -> list[SearchHit]:
        scores: dict[str, float] = {}
        hit_map: dict[str, SearchHit] = {}

        for rank, hit in enumerate(bm25_hits):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            if hit.chunk_id not in hit_map:
                hit_map[hit.chunk_id] = hit
            else:
                existing = hit_map[hit.chunk_id]
                hit_map[hit.chunk_id] = SearchHit(
                    **{**existing.model_dump(), "source_type": "hybrid"}
                )

        for rank, hit in enumerate(vector_hits):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            if hit.chunk_id not in hit_map:
                hit_map[hit.chunk_id] = hit
            else:
                existing = hit_map[hit.chunk_id]
                hit_map[hit.chunk_id] = SearchHit(
                    **{**existing.model_dump(), "source_type": "hybrid"}
                )

        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
        result = []
        for cid in sorted_ids[:top_k]:
            hit = hit_map[cid]
            result.append(
                SearchHit(
                    **{**hit.model_dump(), "similarity_score": scores[cid]}
                )
            )
        return result
