# RAG Knowledge Base

企业级知识库问答系统，支持 PDF/Markdown/HTML 等多格式文档上传、混合检索（向量+全文+Rerank）、LLM 流式问答、引用溯源、代码高亮一键复制。

## ✨ 功能特性

### 🎯 核心能力

- **多格式文档支持** — TXT、Markdown、HTML、PDF（含页码感知分块、元数据提取、目录提取）
- **混合检索引擎** — 向量检索 + 全文检索 + RRF 倒数排名融合
- **Rerank 重排** — 基于语义的二次排序，提升检索准确率
- **LLM 流式问答** — SSE 逐字输出，支持多轮对话上下文
- **引用溯源** — 回答标注来源文档和页码，可跳转查看原文
- **异步处理** — 大文件（>10MB）/ PDF 自动走异步任务队列，上传立即返回
- **Markdown 渲染** — 回答支持 Markdown 格式渲染，代码块语法高亮
- **一键复制** — 整段回答一键复制，代码块独立复制按钮

### 🔐 管理能力

- **用户认证** — JWT + PBKDF2 密码哈希，注册/登录/刷新/登出
- **知识库管理** — 创建/编辑/删除，可见性控制（public/private），成员权限
- **文档管理** — 上传/删除/重命名/在线编辑/重新解析/拖拽上传
- **对话历史** — 多对话管理，消息持久化，引用保存

### 🛠️ 技术架构

- **多后端可切换** — 所有核心组件支持 Provider 模式，可配置切换
- **本地零依赖** — SQLite + Qdrant 本地模式，无需额外服务即可跑通
- **生产就绪** — Docker Compose 一键部署，限流/日志/安全头/CORS 一应俱全
- **优雅降级** — OpenSearch 连接失败自动降级到 PostgreSQL 全文检索

## 🏗️ 架构总览

```
┌───────────────────────────────────────────────────────────┐
│                        Frontend                            │
│  Next.js 14 + React + TypeScript + Tailwind CSS            │
│  工作台 / 知识库 / 文档管理 / 聊天问答 / 检索               │
│  Markdown渲染 / 代码高亮 / 一键复制 / 拖拽上传              │
└───────────────────────────┬───────────────────────────────┘
                            │ REST API + SSE
┌───────────────────────────▼───────────────────────────────┐
│                     Backend (FastAPI)                       │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────────┐  │
│  │   Auth   │  │ Knowledge  │  │      Documents        │  │
│  │  (JWT)   │  │    Base    │  │  (上传/解析/分块)     │  │
│  └──────────┘  └────────────┘  └───────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              RAG Orchestrator                        │   │
│  │  检索 → 重排 → 上下文构建 → LLM 生成 → 流式输出      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────────┐  │
│  │  Vector  │  │  Full-Text │  │   Reranker            │  │
│  │  Search  │  │   Search   │  │  (语义重排)           │  │
│  └────┬─────┘  └─────┬──────┘  └───────────────────────┘  │
└───────┼──────────────┼─────────────────────────────────────┘
        │              │
        ▼              ▼
  ┌──────────┐   ┌────────────┐
  │  Qdrant  │   │ PostgreSQL │
  │  (向量)  │   │  / SQLite  │
  └──────────┘   └────────────┘
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐生产部署）

1. 启动整套服务：

```powershell
docker compose -f infra/docker/docker-compose.yml up -d --build
```

2. 初始化数据库和默认管理员：

```powershell
powershell -File scripts/init-local.ps1
```

3. 访问前端：http://localhost:3000

4. 验证后端：http://localhost:8000/api/v1/health

默认管理员账号（来自 `backend/.env.example`）：
- 邮箱：`admin@example.com`
- 密码：`ChangeMe123!`

### 方式二：本地开发（零依赖）

本地开发模式使用 SQLite + Qdrant 本地模式，无需启动任何外部服务。

**后端：**

```powershell
cd backend
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```powershell
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

> 配置 DashScope API Key（可选）：编辑 `backend/.env` 中的 `DASHSCOPE_API_KEY`，开启真实的 LLM、Embedding 和 Rerank。

## 📁 项目结构

```
RAG/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # API 版本路由
│   │   ├── core/               # 配置、安全、存储、任务队列
│   │   ├── db/                 # 数据库连接
│   │   ├── middleware/         # 限流、日志、安全头、CORS、GZip
│   │   ├── models/             # SQLAlchemy 数据模型（7张表）
│   │   ├── routers/            # API 端点
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── scripts/            # 初始化脚本
│   │   ├── services/
│   │   │   ├── embeddings/     # 嵌入模型（DashScope / Mock）
│   │   │   ├── vector_store/   # 向量存储（Qdrant / Memory）
│   │   │   ├── fulltext/       # 全文搜索（PostgreSQL / OpenSearch）
│   │   │   ├── rerankers/      # 重排器（DashScope / Mock）
│   │   │   ├── llm/            # LLM 客户端（OpenAI 兼容 / Echo）
│   │   │   ├── retrieval/      # 混合检索（RRF 融合）
│   │   │   ├── ingestion/      # 文档摄取（PDF解析+清洗+分块）
│   │   │   └── rag/            # RAG 编排器
│   │   └── workers/            # 异步任务 Worker
│   ├── alembic/                # 数据库迁移
│   └── tests/                  # 测试
├── frontend/                   # Next.js 14 前端
│   ├── app/                    # App Router 页面
│   │   ├── page.tsx            # 工作台
│   │   ├── login/page.tsx      # 登录/注册
│   │   ├── kb/page.tsx         # 知识库列表
│   │   ├── kb/[id]/page.tsx    # 知识库详情（文档管理）
│   │   ├── chat/page.tsx       # 聊天问答
│   │   └── search/page.tsx     # 检索页面
│   ├── components/             # UI 组件（MarkdownMessage、ui）
│   └── lib/                    # API 封装 + 类型定义
├── infra/docker/               # Docker Compose 部署
├── scripts/                    # 初始化脚本
└── docs/                       # 文档
```

## ⚙️ 配置说明

### 核心配置项（`backend/.env`）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| **基础配置** | | |
| `PROJECT_NAME` | `RAG Knowledge Base` | 项目名称 |
| `ENVIRONMENT` | `local` | 运行环境 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_JSON_FORMAT` | `false` | JSON 格式日志 |
| **安全与限流** | | |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT 密钥（生产环境必须修改） |
| `CORS_ORIGINS` | `["*"]` | 允许的 CORS 来源 |
| `ENABLE_RATE_LIMIT` | `false` | 是否启用 API 限流 |
| `RATE_LIMIT_PER_MINUTE` | `60` | 每分钟请求限制 |
| `RATE_LIMIT_PER_HOUR` | `1000` | 每小时请求限制 |
| **文件上传** | | |
| `MAX_UPLOAD_SIZE_MB` | `50` | 最大上传文件大小（MB） |
| `ASYNC_PROCESS_THRESHOLD_MB` | `10` | 异步处理文件大小阈值 |
| `STORAGE_BACKEND` | `local` | 文件存储后端（local / minio） |
| `LOCAL_STORAGE_DIR` | `work/storage` | 本地存储目录 |
| **PDF 处理** | | |
| `PDF_PARSER_BACKEND` | `auto` | PDF 解析后端（auto / pymupdf / pypdf） |
| `PDF_ENABLE_TOC` | `true` | 是否提取 PDF 目录 |
| `PDF_ENABLE_TABLE_EXTRACT` | `false` | PDF 表格提取（默认关闭，避免噪声） |
| **数据库** | | |
| `DATABASE_URL` | `postgresql+asyncpg://rag:rag@localhost:5432/rag_kb` | 数据库连接（支持 PostgreSQL / SQLite） |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| **向量存储** | | |
| `VECTOR_STORE_BACKEND` | `memory` | 向量存储（qdrant / memory） |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant 服务地址 |
| `QDRANT_PATH` | `""` | Qdrant 本地模式数据目录（设为路径启用本地模式） |
| `QDRANT_COLLECTION` | `rag_chunks` | Qdrant 集合名 |
| `EMBEDDING_DIM` | `1024` | 嵌入向量维度 |
| **全文搜索** | | |
| `FULLTEXT_SEARCH_BACKEND` | `postgresql` | 全文搜索（postgresql / opensearch） |
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch 地址 |
| `OPENSEARCH_INDEX` | `rag_chunks` | OpenSearch 索引名 |
| `OPENSEARCH_USE_IK_ANALYZER` | `true` | 是否使用 IK 分词器 |
| **LLM / Embedding / Rerank** | | |
| `DEFAULT_LLM_PROVIDER` | `echo` | LLM 后端（dashscope / openai / echo） |
| `DEFAULT_EMBEDDING_PROVIDER` | `mock` | 嵌入模型后端（dashscope / mock） |
| `DEFAULT_RERANKER_PROVIDER` | `mock` | 重排器后端（dashscope / mock） |
| `DASHSCOPE_API_KEY` | `""` | DashScope API Key |
| `LLM_API_KEY` | `""` | OpenAI 兼容 LLM API Key |
| `LLM_BASE_URL` | `""` | OpenAI 兼容 LLM Base URL |
| `EMBEDDING_API_KEY` | `""` | Embedding API Key |
| `EMBEDDING_BASE_URL` | `""` | Embedding Base URL |
| **对象存储** | | |
| `OBJECT_STORAGE_URL` | `http://localhost:9000` | MinIO 地址 |
| `OBJECT_STORAGE_ACCESS_KEY` | `minio` | MinIO Access Key |
| `OBJECT_STORAGE_SECRET_KEY` | `minio12345` | MinIO Secret Key |
| `OBJECT_STORAGE_BUCKET` | `rag-documents` | MinIO Bucket 名称 |

### 前端配置（`frontend/.env.local`）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | 后端 API 地址 |

## 🧩 API 概览

| 模块 | 端点 | 方法 | 说明 |
|---|---|---|---|
| **健康检查** | `/health` | GET | 系统健康状态（API/DB/向量/全文/Redis） |
| **认证** | `/auth/register` | POST | 用户注册 |
| | `/auth/login` | POST | 用户登录 |
| | `/auth/refresh` | POST | 刷新 Token |
| | `/auth/me` | GET | 获取当前用户 |
| **知识库** | `/knowledge-bases` | GET | 知识库列表 |
| | `/knowledge-bases` | POST | 创建知识库 |
| | `/knowledge-bases/{id}` | GET | 知识库详情 |
| | `/knowledge-bases/{id}` | PATCH | 更新知识库 |
| | `/knowledge-bases/{id}` | DELETE | 删除知识库 |
| **文档** | `/knowledge-bases/{id}/documents/upload` | POST | 上传文档 |
| | `/documents/{id}` | GET | 文档详情 |
| | `/documents/{id}` | DELETE | 删除文档 |
| | `/documents/{id}/chunks` | GET | Chunk 列表 |
| | `/documents/{id}/preview` | GET | 文档预览 |
| | `/documents/{id}/reprocess` | POST | 重新解析 |
| | `/documents/{id}/rename` | PATCH | 重命名 |
| | `/documents/{id}/content` | PUT | 更新内容 |
| **检索** | `/search` | POST | 混合检索 |
| | `/qa/stream` | POST | 流式问答（无对话） |
| **对话** | `/conversations` | GET | 对话列表 |
| | `/conversations` | POST | 创建对话 |
| | `/conversations/{id}` | DELETE | 删除对话 |
| | `/conversations/{id}/messages` | GET | 消息列表 |
| | `/conversations/{id}/messages/stream` | POST | 流式发送消息 |

## 📝 开发说明

### 数据模型（7 张核心表）

- **User** — 用户表（邮箱、密码哈希、角色）
- **KnowledgeBase** — 知识库（名称、描述、可见性、设置）
- **KnowledgeBaseMember** — 知识库成员（角色权限）
- **Document** — 文档（文件名、SHA256、解析状态、元数据）
- **DocumentChunk** — 文档分块（内容、页码范围 page_start/page_end、Token 数）
- **IngestionJob** — 摄取任务（异步处理状态、错误信息、重试次数）
- **Conversation** — 对话（标题、模式、关联知识库）
- **Message** — 消息（角色、内容、引用、Token 使用）

### PDF 处理 Pipeline

```
PDF文件 → PDFParser (PyMuPDF/pypdf)
  → 提取页面文本 (带页码)
  → 提取元数据 (标题/作者/页数/...)
  → 提取目录 (TOC，可选)
  → 提取表格 (Markdown格式，可选，默认关闭)
  → TextCleaner (去噪/修复连字符/去页眉页脚)
  → PageAwareChunker (页码感知分块，保留page_start/page_end)
  → 向量化 → 存入向量库 + 全文索引
```

### 中间件顺序（外 → 内）

CORS → SecurityHeaders → GZip → RateLimit → RequestId → AccessLog

### 添加新的 Embedding Provider

1. 继承 `BaseEmbeddingProvider` 实现 `embed()` 和 `embed_batch()`
2. 在 `services/embeddings/router.py` 中注册
3. 在 `.env` 中配置 `DEFAULT_EMBEDDING_PROVIDER=your_provider`

其他组件（Vector Store、Full-Text、LLM、Reranker）的扩展方式相同。

### 关键设计决策

- **Qdrant 单例懒加载** — 避免重复创建客户端连接
- **OpenSearch 连接池** — `RequestsHttpConnection` + `pool_maxsize=10`
- **IK 分词器自动检测** — 存在则用 `ik_max_word` 索引 / `ik_smart` 搜索，否则降级标准分词器
- **异步元数据前置** — 解析元数据在向量化之前持久化，防止嵌入失败丢失数据
- **DashScope 批量限制** — Embedding API 每批不超过 10 条，避免 400 错误
- **数据库连接池** — `pool_size=20, max_overflow=10, pool_recycle=3600s`

## 📄 License

MIT
