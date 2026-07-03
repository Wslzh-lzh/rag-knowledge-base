from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.common import Base, UUIDTimestampMixin, JSONField


class KnowledgeBase(UUIDTimestampMixin, Base):
    __tablename__ = "knowledge_bases"

    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="private", nullable=False)
    settings: Mapped[dict] = mapped_column(JSONField, default=dict)

    owner = relationship("User", back_populates="owned_knowledge_bases")
    members = relationship("KnowledgeBaseMember", back_populates="knowledge_base", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="knowledge_base", cascade="all, delete-orphan")


class KnowledgeBaseMember(UUIDTimestampMixin, Base):
    __tablename__ = "knowledge_base_members"
    __table_args__ = (UniqueConstraint("kb_id", "user_id", name="uq_kb_member"),)

    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="viewer", nullable=False)

    knowledge_base = relationship("KnowledgeBase", back_populates="members")

