# RAG Knowledge Base

企业级知识库问答系统，支持 PDF / Markdown / HTML / TXT 等文档上传、混合检索、流式问答、引用来源展示、多轮对话与基础知识库管理。

## 功能概览

### 核心能力

- 多格式文档解析：支持 `txt`、`md`、`markdown`、`html`、`htm`、`pdf`
- 混合检索：向量检索 + 全文检索 + Rerank
- 流式问答：基于 SSE 逐步返回回答内容
- 引用来源：回答可展示文档名与页码范围
- 异步处理：大文件和 PDF 支持异步入库
- 在线文档管理：支持预览、重命名、删除、重新解析、部分文本文件在线编辑
- 对话历史：支持多对话切换与消息持久化

### 当前默认运行模式

- 本地开发默认使用 SQLite，无需先装 PostgreSQL
- 向量存储默认可走内存模式，便于本地快速体验
- 默认 LLM Provider 为 `echo`
- 默认 Embedding / Reranker Provider 为 `mock`

这意味着：即使你没有外部 AI 服务密钥，也可以先把系统跑起来看完整流程。

## 技术栈

- 后端：FastAPI + SQLAlchemy + Pydantic Settings
- 前端：Next.js 14 + React 18 + TypeScript + Tailwind CSS
- 检索：Hybrid Retriever + RAG Orchestrator
- 文档处理：PyMuPDF / pypdf
- 可选外部能力：Qdrant / OpenSearch / DashScope / OpenAI Compatible API

## 项目结构

```text
RAG/
├─ backend/                 # FastAPI 后端
│  ├─ app/
│  │  ├─ core/              # 配置、安全、存储、任务队列
│  │  ├─ db/                # 数据库会话
│  │  ├─ models/            # SQLAlchemy 模型
│  │  ├─ routers/           # API 路由
│  │  ├─ schemas/           # 请求 / 响应模型
│  │  ├─ scripts/           # 初始化脚本
│  │  └─ services/          # 检索、RAG、文档解析等核心服务
│  ├─ tests/                # 后端测试
│  └─ pyproject.toml
├─ frontend/                # Next.js 前端
│  ├─ app/                  # 页面
│  ├─ components/           # UI 组件
│  └─ lib/                  # API 封装与类型
├─ infra/docker/            # Docker Compose 配置
├─ scripts/                 # 本地初始化脚本
└─ docs/                    # 项目文档
```

## 快速开始

### 方式一：本地开发模式

适合直接体验界面与主流程。

#### 1. 启动后端

```powershell
cd backend
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

#### 3. 访问系统

- 前端：http://127.0.0.1:3000
- 后端健康检查：http://127.0.0.1:8000/api/v1/health

#### 4. 默认管理员账号

- 邮箱：`admin@example.com`
- 密码：`Admin123!`

说明：

- 系统启动时会自动初始化数据库表
- 如果管理员已存在，会按当前配置补齐默认值，并同步默认密码

### 方式二：Docker Compose

适合完整环境部署或联调。

```powershell
docker compose -f infra/docker/docker-compose.yml up -d --build
powershell -File scripts/init-local.ps1
```

启动后访问：

- 前端：http://localhost:3000
- 后端：http://localhost:8000/api/v1/health

## 关键配置

后端配置来自 `backend/.env`，核心默认值如下：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `ENVIRONMENT` | `local` | 当前运行环境 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./work/rag_kb.db` | 默认本地 SQLite |
| `BOOTSTRAP_ADMIN_EMAIL` | `admin@example.com` | 默认管理员邮箱 |
| `BOOTSTRAP_ADMIN_PASSWORD` | `Admin123!` | 默认管理员密码 |
| `DEFAULT_LLM_PROVIDER` | `echo` | 默认 LLM |
| `DEFAULT_EMBEDDING_PROVIDER` | `mock` | 默认 Embedding |
| `DEFAULT_RERANKER_PROVIDER` | `mock` | 默认 Reranker |
| `VECTOR_STORE_BACKEND` | `memory` | 默认向量存储 |
| `FULLTEXT_SEARCH_BACKEND` | `postgresql` | 全文检索后端 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | 前端 API 地址 |

如果要接入真实模型，可以按需补充：

- `DASHSCOPE_API_KEY`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_BASE_URL`

## API 概览

以下为当前主用接口：

### 健康检查

- `GET /api/v1/health`

### 认证

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### 知识库

- `GET /api/v1/knowledge-bases`
- `POST /api/v1/knowledge-bases`
- `GET /api/v1/knowledge-bases/{id}`
- `PATCH /api/v1/knowledge-bases/{id}`
- `DELETE /api/v1/knowledge-bases/{id}`

### 文档

- `GET /api/v1/knowledge-bases/{kb_id}/documents`
- `POST /api/v1/knowledge-bases/{kb_id}/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/status`
- `GET /api/v1/documents/{document_id}/preview`
- `GET /api/v1/documents/{document_id}/chunks`
- `PATCH /api/v1/documents/{document_id}/rename`
- `PUT /api/v1/documents/{document_id}/content`
- `POST /api/v1/documents/{document_id}/reprocess`
- `DELETE /api/v1/documents/{document_id}`

### 搜索与问答

- `GET /api/v1/search?query=...&top_k=10&kb_ids=kb-1&kb_ids=kb-2`
- `POST /api/v1/knowledge-bases/{kb_id}/search`
- `POST /api/v1/knowledge-bases/{kb_id}/retrieve`
- `POST /api/v1/knowledge-bases/{kb_id}/qa`
- `POST /api/v1/knowledge-bases/{kb_id}/qa/stream`

### 对话

- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `PATCH /api/v1/conversations/{id}`
- `DELETE /api/v1/conversations/{id}`
- `GET /api/v1/conversations/{id}/messages`
- `POST /api/v1/conversations/{id}/messages`
- `POST /api/v1/conversations/{id}/messages/stream`

## 前端当前体验点

- 首页、登录页、知识库页、搜索页和聊天页已完成一轮中文体验修正
- 聊天中的“引用来源”已支持折叠展开，避免消息卡片过长
- 知识库详情页已补充更清晰的文档状态展示

## 测试与验证

后端测试：

```powershell
python -m pytest backend\tests -v
```

前端构建：

```powershell
cd frontend
npm run build
```

## 已知说明

- 当前仓库中部分旧文档可能仍存在历史乱码，代码主链路不受影响
- 若前端开发服务运行中执行 `next build`，可能因为 `.next` 文件占用出现 `EPERM`
- 若本机无法推送到 GitHub，请优先检查到 `github.com:443` 的网络连通性

## License

MIT
