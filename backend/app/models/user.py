from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.common import Base, UUIDTimestampMixin


class User(UUIDTimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)

    owned_knowledge_bases = relationship("KnowledgeBase", back_populates="owner")
    conversations = relationship("Conversation", back_populates="user")

