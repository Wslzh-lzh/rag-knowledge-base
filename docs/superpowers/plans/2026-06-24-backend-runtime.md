# 后端一键可运行实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让后端在本地 Docker 环境里一键启动，完成数据库初始化、JWT 认证、文档入库、文本检索和基础 RAG 闭环。

**Architecture:** 先把基础设施编排和数据库迁移补齐，再修正当前模型与路由中的占位实现。检索第一版走 PostgreSQL 文本搜索，文档入库先支持本地文件落盘和文本切块，后续再替换为向量库和全文检索引擎。

**Tech Stack:** FastAPI, SQLAlchemy 2 async, Alembic, PostgreSQL, Redis, Qdrant, OpenSearch, MinIO, Docker Compose, pytest.

---

### Task 1: 补齐 Docker 与环境启动骨架

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Create: `.env.example`
- Modify: `infra/docker/docker-compose.yml`
- Modify: `README.md`

- [ ] **Step 1: 写出后端镜像和 compose 依赖**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir /app/backend
COPY backend /app/backend
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 写出本地启动示例环境变量**

```env
DATABASE_URL=postgresql+asyncpg://rag:rag@postgres:5432/rag_kb
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
OPENSEARCH_URL=http://opensearch:9200
OBJECT_STORAGE_URL=http://minio:9000
JWT_SECRET_KEY=change-me
```

- [ ] **Step 3: `docker compose up -d` 后检查端口与健康页**

Run: `docker compose -f infra/docker/docker-compose.yml up -d --build`
Expected: backend, postgres, redis, qdrant, opensearch, minio 都能起来，`/api/v1/health` 返回 `{"status":"ok"}`

### Task 2: 修正数据库模型与迁移入口

**Files:**
- Modify: `backend/app/models/document.py`
- Modify: `backend/app/models/knowledge_base.py`
- Modify: `backend/app/models/conversation.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/20260624_0001_init.py`

- [ ] **Step 1: 为保留字段改名并保留 ORM 映射**

```python
metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
```

- [ ] **Step 2: 让 Alembic 正确使用 async 数据库 URL**

```python
from sqlalchemy.ext.asyncio import async_engine_from_config
connectable = async_engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)
```

- [ ] **Step 3: 生成首个迁移，创建 users / knowledge_bases / documents / chunks / jobs / conversations / messages / members 表**

Run: `alembic upgrade head`
Expected: 数据库里出现全部基础表，迁移可重复执行且无报错

### Task 3: 跑通认证与当前用户解析

**Files:**
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/app/core/auth.py`
- Modify: `backend/app/schemas/auth.py`

- [ ] **Step 1: 注册时处理重复邮箱与 token 刷新**

```python
async def register(...):
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ValueError("email_exists")
```

- [ ] **Step 2: `/refresh` 验证 refresh token 并重新签发 token**

```python
payload = decode_token(token)
if payload["type"] != "refresh":
    raise HTTPException(status_code=401, detail="Invalid token type")
```

- [ ] **Step 3: 给 `/me` 和后续路由提供稳定的当前用户对象**

Run: `pytest backend/tests/test_auth.py -v`
Expected: 注册、登录、`/me` 的成功与失败路径都通过

### Task 4: 实现文档入库与检索闭环

**Files:**
- Modify: `backend/app/services/document_service.py`
- Modify: `backend/app/services/ingestion/pipeline.py`
- Modify: `backend/app/services/retrieval/hybrid.py`
- Modify: `backend/app/services/rag/orchestrator.py`
- Modify: `backend/app/routers/documents.py`
- Modify: `backend/app/routers/search.py`
- Modify: `backend/app/schemas/search.py`

- [ ] **Step 1: 上传文件时保存元数据、切块、落库**

```python
parsed = pipeline.process(temp_path)
doc = await service.create_document(...)
for chunk in parsed.chunks:
    await service.create_chunk(db, document_id=doc.id, kb_id=kb_id, ...)
```

- [ ] **Step 2: 检索先走 PostgreSQL 文本搜索并返回 SearchHit**

```python
stmt = select(DocumentChunk).where(DocumentChunk.kb_id.in_(request.knowledge_base_ids))
```

- [ ] **Step 3: RAG 先拼接检索上下文，再调用 LLM 适配器；无外部 LLM 时返回可读 fallback**

Run: `pytest backend/tests/test_documents.py -v`
Expected: 上传、切块、检索、QA 的主路径通过

### Task 5: 补充启动脚本与验收说明

**Files:**
- Create: `scripts/init-local.ps1`
- Modify: `README.md`

- [ ] **Step 1: 提供一键初始化脚本**

```powershell
docker compose -f infra/docker/docker-compose.yml up -d --build
python -m alembic upgrade head
```

- [ ] **Step 2: 在 README 里写出完整启动顺序和验证命令**

Run: `curl http://localhost:8000/api/v1/health`
Expected: 返回 `{"status":"ok"}`

