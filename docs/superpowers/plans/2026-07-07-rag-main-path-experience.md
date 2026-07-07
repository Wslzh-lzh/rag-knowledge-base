# RAG Main Path Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复从登录到问答主路径上的关键体验问题，并同步收口直接影响体验的后端稳定性问题。

**Architecture:** 以用户主路径为主线推进整改，前端侧统一文案、状态与错误反馈，后端侧消除配置隐式耦合、接口契约不一致和文档状态不透明的问题。每个任务都包含对应回归测试，优先保证默认本地开发模式可预测、可验证。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic Settings, Next.js 14, React 18, TypeScript, pytest, TestClient

---

### Task 1: 稳定默认配置与 RAG 回退行为

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/services/rag/orchestrator.py`
- Modify: `backend/tests/test_rag_orchestrator.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: 写出会失败的 RAG 回退测试**

```python
from unittest.mock import AsyncMock

from app.services.rag.orchestrator import RAGOrchestrator, RAGState


class FakeRetriever:
    async def retrieve(self, request):
        return []


async def test_answer_uses_fallback_when_llm_provider_is_echo() -> None:
    orchestrator = RAGOrchestrator(
        retriever=FakeRetriever(),
        llm_client=AsyncMock(),
        llm_provider="echo",
    )

    result = await orchestrator.answer(RAGState(query="test"))

    assert result.retrieval_debug["mode"] == "fallback_summary"
```

- [ ] **Step 2: 运行测试并确认它先失败**

Run: `python -m pytest backend/tests/test_rag_orchestrator.py -v`
Expected: FAIL，报 `__init__` 不支持 `llm_client` 或 `llm_provider`

- [ ] **Step 3: 最小实现显式依赖注入与默认行为解耦**

```python
class RAGOrchestrator:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        llm_client=None,
        llm_provider: str | None = None,
    ) -> None:
        self.retriever = retriever or HybridRetriever()
        self.llm = llm_client or get_llm_client()
        self.llm_provider = llm_provider or settings.default_llm_provider
        self.summarizer = FallbackSummarizer()

    def _use_fallback_summary(self) -> bool:
        return self.llm_provider == "echo"
```

- [ ] **Step 4: 同步把 `answer()` 和 `answer_stream()` 改成读取实例级 provider**

```python
if self._use_fallback_summary():
    answer = self.summarizer.summarize(state.query, hits)
    usage = {"prompt_tokens": 0, "completion_tokens": len(answer), "total_tokens": len(answer)}
    return QAResponse(
        answer=answer,
        citations=hits,
        usage=usage,
        retrieval_debug={"retrieved": len(hits), "mode": "fallback_summary"},
    )
```

- [ ] **Step 5: 补一个配置测试，确保测试环境不依赖本地 `.env` 才能稳定跑**

```python
from app.core.config import Settings


def test_settings_allows_runtime_override() -> None:
    settings = Settings(DEFAULT_LLM_PROVIDER="echo")
    assert settings.default_llm_provider == "echo"
```

- [ ] **Step 6: 重新运行相关测试确认通过**

Run: `python -m pytest backend/tests/test_rag_orchestrator.py backend/tests/test_config.py -v`
Expected: PASS，且不再尝试连接外部 LLM

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/config.py backend/app/services/rag/orchestrator.py backend/tests/test_rag_orchestrator.py backend/tests/test_config.py
git commit -m "fix: stabilize rag fallback configuration"
```

### Task 2: 统一搜索接口契约并补回归测试

**Files:**
- Modify: `backend/app/routers/search.py`
- Modify: `backend/tests/test_health_api.py`
- Create: `backend/tests/test_search_api.py`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/search/page.tsx`

- [ ] **Step 1: 写出搜索接口知识库过滤的失败测试**

```python
from fastapi.testclient import TestClient


def test_search_accepts_kb_ids_query_param(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"query": "leave", "kb_ids": ["kb-1"]})
    assert response.status_code == 200
```

- [ ] **Step 2: 运行测试并确认它先失败或表现不符合预期**

Run: `python -m pytest backend/tests/test_search_api.py -v`
Expected: FAIL，或虽然 200 但检索请求未带上 `knowledge_base_ids`

- [ ] **Step 3: 最小实现后端 `/search` 接收 `kb_ids` 并传给检索层**

```python
@router.get("/search", response_model=list[SearchHit])
async def search(
    query: str,
    top_k: int = 10,
    kb_ids: list[str] | None = None,
    use_vector_search: bool = True,
    use_bm25: bool = True,
    use_reranker: bool = True,
) -> list[SearchHit]:
    return await retriever.retrieve(
        RetrievalRequest(
            query=query,
            knowledge_base_ids=kb_ids or [],
            top_k=top_k,
            use_vector_search=use_vector_search,
            use_bm25=use_bm25,
            use_reranker=use_reranker,
        )
    )
```

- [ ] **Step 4: 前端改成显式传入当前筛选知识库并给出空结果提示**

```typescript
const data = await api.search(query, 10, selectedKb ? [selectedKb] : undefined);
setResults(data);
setError(null);
```

- [ ] **Step 5: 在搜索页新增知识库筛选 UI 所需的最小状态**

```typescript
const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
const [selectedKb, setSelectedKb] = useState<string>("");
```

- [ ] **Step 6: 重新运行搜索相关测试**

Run: `python -m pytest backend/tests/test_search_api.py -v`
Expected: PASS，接口契约与前端调用一致

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/search.py backend/tests/test_search_api.py frontend/lib/api.ts frontend/app/search/page.tsx
git commit -m "fix: align search api with kb filters"
```

### Task 3: 修复主路径前端中文乱码与统一错误反馈

**Files:**
- Modify: `frontend/app/login/page.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/search/page.tsx`
- Modify: `frontend/app/chat/page.tsx`
- Modify: `frontend/components/MarkdownMessage.tsx`
- Create: `frontend/lib/messages.ts`
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: 先新增统一文案常量文件，避免页面里继续散落乱码字符串**

```typescript
export const messages = {
  loading: "正在加载数据...",
  loadingMessages: "正在加载消息...",
  sessionExpired: "登录状态已失效，请重新登录",
  unknownError: "系统开小差了，请稍后再试",
  emptyConversations: "暂无对话",
  emptyKnowledgeBases: "暂无知识库",
};
```

- [ ] **Step 2: 运行一次前端构建前检查，确认当前页面存在文案问题但构建逻辑不先改**

Run: `npm run build`
Expected: 可能仍失败，但此步用于记录当前状态；页面文案乱码尚未修复

- [ ] **Step 3: 在首页、聊天页、搜索页、登录页替换乱码文案为统一消息**

```typescript
{error ?? messages.unknownError}
```

- [ ] **Step 4: 在 API 层提取统一错误转换函数**

```typescript
export function toUserMessage(error: unknown): string {
  const text = error instanceof Error ? error.message : "";
  if (text.includes("401") || text.includes("403")) return messages.sessionExpired;
  return messages.unknownError;
}
```

- [ ] **Step 5: 聊天代码块复制和答案复制按钮统一为可读中文**

```tsx
<span>{copied ? "已复制" : "复制回答"}</span>
```

- [ ] **Step 6: 运行前端构建验证改动未引入新的类型错误**

Run: `npm run build`
Expected: 至少不因新增代码报 TypeScript 错误；若仍有 `.next/trace` 权限问题，记录为环境问题并改用 `npm run lint` 或类型检查补证

- [ ] **Step 7: Commit**

```bash
git add frontend/app/login/page.tsx frontend/app/page.tsx frontend/app/search/page.tsx frontend/app/chat/page.tsx frontend/components/MarkdownMessage.tsx frontend/lib/api.ts frontend/lib/messages.ts
git commit -m "fix: normalize main path frontend copy"
```

### Task 4: 强化登录态、首页与聊天首屏状态

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/chat/page.tsx`
- Modify: `frontend/app/kb/page.tsx`
- Modify: `frontend/app/kb/[id]/page.tsx`
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: 写出一个最小页面状态规则清单，先按这个规则改实现**

```typescript
type PageState = "loading" | "ready" | "empty" | "error";
```

- [ ] **Step 2: 首页改为并行请求失败时尽量保留部分可用内容，不让首屏整体报废**

```typescript
const [meResult, kbResult, convResult] = await Promise.allSettled([
  api.me(),
  api.listKnowledgeBases(),
  api.listConversations(),
]);
```

- [ ] **Step 3: 聊天页在没有知识库、没有会话、切换知识库时给出明确空状态**

```typescript
if (kbs.length === 0) {
  setError("请先创建一个知识库，再开始提问。");
  setCurrentConv(null);
  setMessages([]);
  return;
}
```

- [ ] **Step 4: 知识库页与详情页统一处理未登录跳转和接口失败提示**

```typescript
if (err.message?.includes("401") || err.message?.includes("403")) {
  clearToken();
  router.push("/login");
  return;
}
```

- [ ] **Step 5: 通过页面级 smoke check 验证状态分支不互相冲突**

Run: `npm run build`
Expected: 页面状态逻辑通过编译，条件分支无明显类型错误

- [ ] **Step 6: Commit**

```bash
git add frontend/app/page.tsx frontend/app/chat/page.tsx frontend/app/kb/page.tsx frontend/app/kb/[id]/page.tsx frontend/lib/api.ts
git commit -m "fix: harden main path page states"
```

### Task 5: 提升文档上传与处理状态可见性

**Files:**
- Modify: `backend/app/routers/documents.py`
- Modify: `backend/app/services/document_service.py`
- Modify: `backend/app/schemas/document.py`
- Create: `backend/tests/test_documents_api.py`
- Modify: `frontend/app/kb/[id]/page.tsx`
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: 写出文档状态接口的失败测试**

```python
def test_document_status_returns_pending_message(client: TestClient) -> None:
    response = client.get("/api/v1/documents/doc-1/status")
    assert response.status_code in {200, 404}
```

- [ ] **Step 2: 运行测试并确认当前缺少完整状态语义**

Run: `python -m pytest backend/tests/test_documents_api.py -v`
Expected: FAIL，或返回字段不足以区分 pending / processing / completed / failed

- [ ] **Step 3: 后端补齐状态消息与失败语义**

```python
message_map = {
    "pending": "文档已接收，等待处理",
    "processing": "文档正在处理中",
    "completed": "文档处理完成",
    "empty": "文档已处理，但未提取到有效内容",
    "failed": "文档处理失败，请重试或检查文件内容",
}
```

- [ ] **Step 4: 前端知识库详情页轮询待处理文档状态，并展示状态徽标**

```typescript
if (doc.parse_status === "pending" || doc.parse_status === "processing") {
  window.setTimeout(() => refreshDocuments(), 2000);
}
```

- [ ] **Step 5: 上传、重处理、编辑完成后统一刷新文档列表和提示文案**

```typescript
await api.reprocessDocument(doc.id);
await refreshDocuments();
setNotice("已重新提交处理任务");
```

- [ ] **Step 6: 重新运行文档相关测试**

Run: `python -m pytest backend/tests/test_documents_api.py -v`
Expected: PASS，状态语义完整可用

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/documents.py backend/app/services/document_service.py backend/app/schemas/document.py backend/tests/test_documents_api.py frontend/app/kb/[id]/page.tsx frontend/lib/api.ts
git commit -m "fix: surface document processing states"
```

### Task 6: 收口聊天与搜索主链路并做整体验证

**Files:**
- Modify: `frontend/app/chat/page.tsx`
- Modify: `frontend/app/search/page.tsx`
- Modify: `frontend/components/MarkdownMessage.tsx`
- Modify: `backend/tests/test_rag_orchestrator.py`
- Modify: `backend/tests/test_search_api.py`

- [ ] **Step 1: 为聊天流式回答补一个最小回归断言**

```python
async def test_answer_uses_retrieved_context() -> None:
    orchestrator = RAGOrchestrator(retriever=FakeRetriever(), llm_provider="echo")
    result = await orchestrator.answer(RAGState(query="How is annual leave approved?", knowledge_base_ids=["kb-1"]))
    assert "annual leave" in result.answer.lower()
```

- [ ] **Step 2: 运行后端主链路测试确认先红后绿完整闭环**

Run: `python -m pytest backend/tests/test_rag_orchestrator.py backend/tests/test_search_api.py -v`
Expected: 先在修改前失败，完成后 PASS

- [ ] **Step 3: 聊天页统一引用展示、复制按钮和错误提示**

```tsx
<p className="text-xs font-medium mb-2 text-muted">引用来源</p>
```

- [ ] **Step 4: 搜索页统一“加载中 / 无结果 / 失败”文案与知识库筛选体验**

```tsx
<div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-muted text-center">
  没有找到相关结果，试试更换关键词或切换知识库筛选。
</div>
```

- [ ] **Step 5: 跑完整后端测试与前端构建，作为本轮阶段性验收**

Run: `python -m pytest backend/tests -v`
Expected: PASS 或仅剩与本轮无关的既有失败项并已明确记录

Run: `npm run build`
Expected: 成功；如果仍出现 `.next/trace` 权限问题，则补跑一次不写产物的验证命令并记录环境限制

- [ ] **Step 6: 手动按主路径做最终验证**

Run:
- `登录 -> 首页 -> 知识库 -> 上传文档 -> 搜索 -> 聊天问答`

Expected:
- 文案可读
- 状态可理解
- 搜索与问答结果结构一致
- 失败时有明确提示

- [ ] **Step 7: Commit**

```bash
git add frontend/app/chat/page.tsx frontend/app/search/page.tsx frontend/components/MarkdownMessage.tsx backend/tests/test_rag_orchestrator.py backend/tests/test_search_api.py
git commit -m "feat: polish main path search and chat experience"
```
