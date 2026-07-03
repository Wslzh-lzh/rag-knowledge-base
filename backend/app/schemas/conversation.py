from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ConversationCreate(BaseModel):
    kb_id: str | None = None
    title: str | None = None
    mode: str = "rag"


class ConversationUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None


class ConversationRead(ORMModel):
    id: str
    kb_id: str | None = None
    user_id: str
    title: str
    summary: str | None = None
    mode: str


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageRead(ORMModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: list
    usage: dict

