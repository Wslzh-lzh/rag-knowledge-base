from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    visibility: str = "private"
    settings: dict = Field(default_factory=dict)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    settings: dict | None = None


class KnowledgeBaseRead(ORMModel):
    id: str
    owner_id: str
    name: str
    description: str | None = None
    visibility: str
    settings: dict


class KnowledgeBaseMemberRead(ORMModel):
    id: str
    kb_id: str
    user_id: str
    role: str

