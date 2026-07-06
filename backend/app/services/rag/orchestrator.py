from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import AsyncIterator

from app.schemas.search import QAResponse, SearchHit
from app.services.llm.base import LLMMessage
from app.services.llm.router import get_llm_client
from app.services.retrieval.hybrid import HybridRetriever, RetrievalRequest


SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据以下检索到的文档片段回答用户的问题。

回答要求：
1. 只基于提供的上下文信息回答，不要编造信息
2. 如果上下文中没有相关信息，请明确告知用户
3. 回答要准确、简洁、有条理
4. 引用来源时使用 [n] 格式标注在句子末尾，其中 n 是来源编号
5. 结合对话历史理解用户问题，保持上下文连贯性"""


@dataclass
class RAGState:
    query: str
    knowledge_base_ids: list[str] = field(default_factory=list)
    conversation_history: list[LLMMessage] = field(default_factory=list)
    metadata_filter: dict = field(default_factory=dict)
    top_k: int = 10
    use_vector_search: bool = True
    use_bm25: bool = True
    use_reranker: bool = True


def _format_page_range(page_start: int | None, page_end: int | None) -> str:
    if page_start and page_end:
        if page_start == page_end:
            return f"第 {page_start} 页"
        else:
            return f"第 {page_start}-{page_end} 页"
    return ""


class FallbackSummarizer:
    @staticmethod
    def _extract_sentences(text: str, max_sentences: int = 3) -> list[str]:
        sentences = re.split(r"(?<=[。！？.!?])\s*", text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences[:max_sentences]

    @staticmethod
    def summarize(query: str, hits: list[SearchHit], max_chars: int = 800) -> str:
        if not hits:
            return "未找到与您问题相关的内容。请尝试用不同的关键词搜索，或检查知识库中是否已上传相关文档。"

        top_hits = hits[:3]
        answer_parts: list[str] = []
        char_count = 0

        for i, hit in enumerate(top_hits):
            sentences = FallbackSummarizer._extract_sentences(hit.content, max_sentences=2)
            snippet = " ".join(sentences) if sentences else hit.content[:300]
            if not snippet.strip():
                continue

            source = hit.document_name or f"文档 {i+1}"
            page_info = _format_page_range(hit.page_start, hit.page_end)
            if page_info:
                prefix = f"【来源：{source}（{page_info}）】"
            else:
                prefix = f"【来源：{source}】"
            if char_count + len(prefix) + len(snippet) + 2 > max_chars and answer_parts:
                break

            answer_parts.append(f"{prefix}{snippet}")
            char_count += len(prefix) + len(snippet)

        if not answer_parts:
            return "找到了相关文档，但未能提取出有效内容摘要。请查看检索结果中的完整内容。"

        intro = f"根据知识库中的 {len(top_hits)} 段相关内容，为您整理如下信息：\n\n"
        answer = intro + "\n\n".join(answer_parts)

        if len(hits) > len(top_hits):
            answer += f"\n\n（还有 {len(hits) - len(top_hits)} 条相关结果未展示，完整列表请查看引用来源）"

        return answer


class RAGOrchestrator:
    def __init__(self, retriever: HybridRetriever | None = None) -> None:
        self.retriever = retriever or HybridRetriever()
        self.llm = get_llm_client()
        self.summarizer = FallbackSummarizer()

    def _build_context(self, hits: list[SearchHit]) -> str:
        context_parts = []
        for i, hit in enumerate(hits[:8], 1):
            source = hit.document_name or f"文档 {i}"
            page_info = _format_page_range(hit.page_start, hit.page_end)
            if page_info:
                header = f"[{i}] {source}（{page_info}）"
            else:
                header = f"[{i}] {source}"
            context_parts.append(f"{header}\n{hit.content}")
        return "\n\n".join(context_parts) if context_parts else "未找到相关内容。"

    def _build_messages(self, state: RAGState, hits: list[SearchHit]) -> list[LLMMessage]:
        context = self._build_context(hits)
        user_prompt = f"用户问题：{state.query}\n\n以下是检索到的文档片段：\n{context}\n\n请根据以上文档片段回答用户的问题。"

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
        ]

        if state.conversation_history:
            messages.extend(state.conversation_history[-10:])

        messages.append(LLMMessage(role="user", content=user_prompt))
        return messages

    async def answer(self, state: RAGState) -> QAResponse:
        hits = await self.retriever.retrieve(
            RetrievalRequest(
                query=state.query,
                knowledge_base_ids=state.knowledge_base_ids,
                top_k=state.top_k,
                metadata_filter=state.metadata_filter,
                use_vector_search=state.use_vector_search,
                use_bm25=state.use_bm25,
                use_reranker=state.use_reranker,
            )
        )

        from app.core.config import settings

        if settings.default_llm_provider == "echo":
            answer = self.summarizer.summarize(state.query, hits)
            usage = {"prompt_tokens": 0, "completion_tokens": len(answer), "total_tokens": len(answer)}
            return QAResponse(
                answer=answer,
                citations=hits,
                usage=usage,
                retrieval_debug={"retrieved": len(hits), "mode": "fallback_summary"},
            )

        messages = self._build_messages(state, hits)
        result = await self.llm.generate(messages)
        return QAResponse(
            answer=result.content,
            citations=hits,
            usage=result.usage,
            retrieval_debug={"retrieved": len(hits), "mode": "llm"},
        )

    async def answer_stream(
        self,
        state: RAGState,
    ) -> AsyncIterator[dict]:
        hits = await self.retriever.retrieve(
            RetrievalRequest(
                query=state.query,
                knowledge_base_ids=state.knowledge_base_ids,
                top_k=state.top_k,
                metadata_filter=state.metadata_filter,
                use_vector_search=state.use_vector_search,
                use_bm25=state.use_bm25,
                use_reranker=state.use_reranker,
            )
        )

        from app.core.config import settings

        if settings.default_llm_provider == "echo":
            answer = self.summarizer.summarize(state.query, hits)
            usage = {"prompt_tokens": 0, "completion_tokens": len(answer), "total_tokens": len(answer)}
            yield {
                "type": "citations",
                "citations": [hit.model_dump() for hit in hits],
            }
            for char in answer:
                yield {"type": "delta", "content": char}
            yield {
                "type": "done",
                "usage": usage,
                "retrieval_debug": {"retrieved": len(hits), "mode": "fallback_summary"},
            }
            return

        messages = self._build_messages(state, hits)
        client = self.llm

        yield {
            "type": "citations",
            "citations": [hit.model_dump() for hit in hits],
        }

        full_content = ""
        if hasattr(client, "generate_stream"):
            async for delta in client.generate_stream(messages):
                full_content += delta
                yield {"type": "delta", "content": delta}
        else:
            result = await client.generate(messages)
            full_content = result.content
            for char in full_content:
                yield {"type": "delta", "content": char}

        yield {
            "type": "done",
            "usage": {"prompt_tokens": 0, "completion_tokens": len(full_content), "total_tokens": len(full_content)},
            "retrieval_debug": {"retrieved": len(hits), "mode": "llm_stream"},
        }
