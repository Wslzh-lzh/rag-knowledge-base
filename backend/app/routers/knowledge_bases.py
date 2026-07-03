from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.deps import get_db
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter()
service = KnowledgeBaseService()


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_knowledge_bases(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)) -> list[KnowledgeBaseRead]:
    items = await service.list(db, owner_id=user.id)
    return [KnowledgeBaseRead.model_validate(item) for item in items]


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(payload: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)) -> KnowledgeBaseRead:
    kb = await service.create(db, owner_id=user.id, name=payload.name, description=payload.description, visibility=payload.visibility, settings=payload.settings)
    return KnowledgeBaseRead.model_validate(kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseRead)
async def get_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)) -> KnowledgeBaseRead:
    kb = await service.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return KnowledgeBaseRead.model_validate(kb)


@router.patch("/{kb_id}", response_model=KnowledgeBaseRead)
async def update_knowledge_base(kb_id: str, payload: KnowledgeBaseUpdate, db: AsyncSession = Depends(get_db)) -> KnowledgeBaseRead:
    kb = await service.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(kb, field, value)
    await db.commit()
    await db.refresh(kb)
    return KnowledgeBaseRead.model_validate(kb)


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    kb = await service.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    await db.delete(kb)
    await db.commit()
    return {"kb_id": kb_id, "status": "deleted"}


@router.post("/{kb_id}/members")
async def add_member(kb_id: str, payload: dict, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)) -> dict:
    member = await service.add_member(db, kb_id=kb_id, user_id=payload["user_id"], role=payload.get("role", "viewer"))
    return {"id": member.id, "status": "created"}
