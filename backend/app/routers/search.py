import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.search import QARequest, QAResponse, SearchRequest, SearchHit
from app.services.rag.orchestrator import RAGOrchestrator, RAGState
from app.services.retrieval.hybrid import HybridRetriever, RetrievalRequest

router = APIRouter()
rag = RAGOrchestrator()
retriever = HybridRetriever()


@router.get("/search", response_model=list[SearchHit])
async def search(
    query: str,
    top_k: int = 10,
    use_vector_search: bool = True,
    use_bm25: bool = True,
    use_reranker: bool = True,
) -> list[SearchHit]:
    return await retriever.retrieve(
        RetrievalRequest(
            query=query,
            top_k=top_k,
            use_vector_search=use_vector_search,
            use_bm25=use_bm25,
            use_reranker=use_reranker,
        )
    )


@router.post("/knowledge-bases/{kb_id}/search", response_model=list[SearchHit])
async def search_in_kb(kb_id: str, payload: SearchRequest) -> list[SearchHit]:
    knowledge_base_ids = payload.knowledge_base_ids or [kb_id]
    return await retriever.retrieve(
        RetrievalRequest(
            query=payload.query,
            knowledge_base_ids=knowledge_base_ids,
            top_k=payload.top_k,
            metadata_filter=payload.metadata_filter,
            use_vector_search=payload.use_vector_search,
            use_bm25=payload.use_bm25,
            use_reranker=payload.use_reranker,
        )
    )


@router.post("/knowledge-bases/{kb_id}/retrieve", response_model=list[SearchHit])
async def retrieve_in_kb(kb_id: str, payload: SearchRequest) -> list[SearchHit]:
    knowledge_base_ids = payload.knowledge_base_ids or [kb_id]
    return await retriever.retrieve(
        RetrievalRequest(
            query=payload.query,
            knowledge_base_ids=knowledge_base_ids,
            top_k=payload.top_k,
            metadata_filter=payload.metadata_filter,
            use_vector_search=payload.use_vector_search,
            use_bm25=payload.use_bm25,
            use_reranker=payload.use_reranker,
        )
    )


@router.post("/knowledge-bases/{kb_id}/qa", response_model=QAResponse)
async def qa(kb_id: str, payload: QARequest) -> QAResponse:
    return await rag.answer(
        RAGState(
            query=payload.query,
            knowledge_base_ids=payload.knowledge_base_ids or [kb_id],
            metadata_filter=payload.metadata_filter,
            top_k=payload.top_k,
            use_vector_search=payload.use_vector_search,
            use_bm25=payload.use_bm25,
            use_reranker=payload.use_reranker,
        )
    )


@router.post("/knowledge-bases/{kb_id}/qa/stream")
async def qa_stream(kb_id: str, payload: QARequest):
    state = RAGState(
        query=payload.query,
        knowledge_base_ids=payload.knowledge_base_ids or [kb_id],
        metadata_filter=payload.metadata_filter,
        top_k=payload.top_k,
        use_vector_search=payload.use_vector_search,
        use_bm25=payload.use_bm25,
        use_reranker=payload.use_reranker,
    )

    async def event_generator():
        async for event in rag.answer_stream(state):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
