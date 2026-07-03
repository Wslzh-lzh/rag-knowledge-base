from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.task_queue import get_task_queue
from app.middleware.logging import AccessLogMiddleware, RequestIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        level=settings.log_level,
        json_format=settings.log_json_format,
    )

    from app.services.ingestion.tasks import register_ingestion_tasks
    register_ingestion_tasks()

    tq = get_task_queue()
    await tq.start()
    logger.info("Application started")

    yield

    tq = get_task_queue()
    await tq.stop()
    logger.info("Application stopped")


def create_app() -> FastAPI:
    setup_logging(
        level=settings.log_level,
        json_format=settings.log_json_format,
    )

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    if settings.enable_rate_limit:
        app.add_middleware(RateLimitMiddleware)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(AccessLogMiddleware)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
