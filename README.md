# RAG Knowledge Base

企业级知识库问答系统骨架，包含：

- FastAPI 后端
- Next.js 前端
- PostgreSQL、Redis、Qdrant、OpenSearch、MinIO
- JWT 认证、文档入库、文本检索和基础 RAG 闭环

## 一键启动

1. 启动整套服务：

```powershell
docker compose -f infra/docker/docker-compose.yml up -d --build
```

2. 初始化数据库和默认管理员：

```powershell
powershell -File scripts/init-local.ps1
```

3. 验证接口：

```powershell
curl http://localhost:8000/api/v1/health
```

默认管理员来自 `backend/.env.example` 里的：

- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD`

## 本地开发

后端本地运行时，先准备数据库和缓存服务，然后执行：

```powershell
cd backend
python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端默认读取 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`。

## 目录

- `backend/`
- `frontend/`
- `infra/docker/docker-compose.yml`
- `scripts/init-local.ps1`

