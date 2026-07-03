from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message


class ConversationService:
    async def create_conversation(self, db: AsyncSession, *, user_id: str, kb_id: str | None, title: str, mode: str) -> Conversation:
        conversation = Conversation(user_id=user_id, kb_id=kb_id, title=title, mode=mode)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def list_conversations(self, db: AsyncSession, user_id: str) -> list[Conversation]:
        result = await db.execute(select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()))
        return list(result.scalars().all())

    async def get_conversation(self, db: AsyncSession, conversation_id: str, user_id: str) -> Conversation | None:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_conversation(self, db: AsyncSession, conversation_id: str, user_id: str, *, title: str | None = None, summary: str | None = None) -> Conversation | None:
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return None
        if title is not None:
            conversation.title = title
        if summary is not None:
            conversation.summary = summary
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def delete_conversation(self, db: AsyncSession, conversation_id: str, user_id: str) -> bool:
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        await db.delete(conversation)
        await db.commit()
        return True

    async def list_messages(self, db: AsyncSession, conversation_id: str, user_id: str) -> list[Message]:
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return []
        result = await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        db: AsyncSession,
        *,
        conversation_id: str,
        role: str,
        content: str,
        citations: list | None = None,
        usage: dict | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            usage=usage or {},
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

