from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    top_k: int = 10
    use_hybrid: bool = True
    use_vector_search: bool = True
    use_bm25: bool = True
    use_reranker: bool = True
    metadata_filter: dict = Field(default_factory=dict)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    kb_id: str
    page_start: int | None = None
    page_end: int | None = None
    content: str
    similarity_score: float
    source_type: str = "vector"
    highlight: str | None = None
    metadata: dict = Field(default_factory=dict)


class QARequest(SearchRequest):
    conversation_id: str | None = None
    stream: bool = False


class QAResponse(BaseModel):
    answer: str
    citations: list[SearchHit] = Field(default_factory=list)
    conversation_id: str | None = None
    trace_id: str | None = None
    usage: dict = Field(default_factory=dict)
    retrieval_debug: dict = Field(default_factory=dict)

