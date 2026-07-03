from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseMember


class KnowledgeBaseService:
    async def list(self, db: AsyncSession, owner_id: str | None = None) -> list[KnowledgeBase]:
        stmt = select(KnowledgeBase)
        if owner_id:
            stmt = stmt.where(KnowledgeBase.owner_id == owner_id)
        result = await db.execute(stmt.order_by(KnowledgeBase.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, owner_id: str, name: str, description: str | None, visibility: str, settings: dict) -> KnowledgeBase:
        kb = KnowledgeBase(owner_id=owner_id, name=name, description=description, visibility=visibility, settings=settings)
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
        return kb

    async def get(self, db: AsyncSession, kb_id: str) -> KnowledgeBase | None:
        return await db.get(KnowledgeBase, kb_id)

    async def add_member(self, db: AsyncSession, *, kb_id: str, user_id: str, role: str) -> KnowledgeBaseMember:
        member = KnowledgeBaseMember(kb_id=kb_id, user_id=user_id, role=role)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

