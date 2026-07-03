from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.conversations import router as conversations_router
from app.routers.documents import router as documents_router
from app.routers.documents import kb_documents_router
from app.routers.health import router as health_router
from app.routers.knowledge_bases import router as knowledge_bases_router
from app.routers.search import router as search_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(knowledge_bases_router, prefix="/knowledge-bases", tags=["knowledge_bases"])
api_router.include_router(kb_documents_router, prefix="/knowledge-bases/{kb_id}", tags=["documents"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(search_router, tags=["search"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])

