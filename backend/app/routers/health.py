from __future__ import annotations

import time

from fastapi import APIRouter

from app.core.config import settings
from app.db.session import async_session_factory
from app.services.fulltext.router import get_fulltext_searcher
from app.services.vector_store.router import get_vector_store

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """统一健康检查接口，检查所有外部服务状态。"""
    overall_status = "healthy"
    services: dict[str, dict] = {}

    services["api"] = {"status": "healthy"}

    db_status = await _check_database()
    services["database"] = db_status
    if db_status["status"] != "healthy":
        overall_status = "degraded"

    vector_status = await _check_vector_store()
    services["vector_store"] = vector_status
    if vector_status["status"] != "healthy":
        overall_status = "degraded"

    fulltext_status = await _check_fulltext_search()
    services["fulltext_search"] = fulltext_status
    if fulltext_status["status"] != "healthy":
        overall_status = "degraded"

    redis_status = await _check_redis()
    services["redis"] = redis_status
    if redis_status["status"] != "healthy":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "version": settings.version,
        "environment": settings.environment,
        "services": services,
    }


async def _check_database() -> dict:
    try:
        async with async_session_factory() as db:
            from sqlalchemy import text

            result = await db.execute(text("SELECT 1"))
            result.scalar()
        return {"status": "healthy", "backend": settings.database_url.split("://")[0]}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_vector_store() -> dict:
    try:
        store = get_vector_store()
        if hasattr(store, "health_check"):
            return await store.health_check()
        return {"status": "healthy", "backend": settings.vector_store_backend}
    except Exception as e:
        return {"status": "unhealthy", "backend": settings.vector_store_backend, "error": str(e)}


async def _check_fulltext_search() -> dict:
    try:
        searcher = get_fulltext_searcher()
        if hasattr(searcher, "health_check"):
            return await searcher.health_check()
        return {"status": "healthy", "backend": settings.fulltext_search_backend}
    except Exception as e:
        return {"status": "unhealthy", "backend": settings.fulltext_search_backend, "error": str(e)}


async def _check_redis() -> dict:
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        await client.ping()
        await client.close()
        return {"status": "healthy"}
    except Exception:
        try:
            import redis

            client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
            client.ping()
            client.close()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
