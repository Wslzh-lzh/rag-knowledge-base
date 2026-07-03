"""init

Revision ID: 20260624_0001
Revises: 
Create Date: 2026-06-24 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260624_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column("settings", JSONB, nullable=False),
    )
    op.create_index("ix_knowledge_bases_owner_id", "knowledge_bases", ["owner_id"], unique=False)

    op.create_table(
        "knowledge_base_members",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kb_id", sa.String(), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.UniqueConstraint("kb_id", "user_id", name="uq_kb_member"),
    )
    op.create_index("ix_knowledge_base_members_kb_id", "knowledge_base_members", ["kb_id"], unique=False)
    op.create_index("ix_knowledge_base_members_user_id", "knowledge_base_members", ["user_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kb_id", sa.String(), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploader_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
    )
    op.create_index("ix_documents_kb_id", "documents", ["kb_id"], unique=False)
    op.create_index("ix_documents_uploader_id", "documents", ["uploader_id"], unique=False)
    op.create_index("ix_documents_kb_status_created", "documents", ["kb_id", "parse_status", "created_at"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kb_id", sa.String(), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_chunk_id", sa.String(), sa.ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chunk_no", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)
    op.create_index("ix_document_chunks_kb_id", "document_chunks", ["kb_id"], unique=False)
    op.create_index("ix_document_chunks_doc_chunk", "document_chunks", ["document_id", "chunk_no"], unique=False)
    op.create_index("ix_document_chunks_kb_page", "document_chunks", ["kb_id", "page_start"], unique=False)

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
    )
    op.create_index("ix_ingestion_jobs_document_id", "ingestion_jobs", ["document_id"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kb_id", sa.String(), sa.ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("mode", sa.String(length=32), nullable=False),
    )
    op.create_index("ix_conversations_kb_id", "conversations", ["kb_id"], unique=False)
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"], unique=False)
    op.create_index("ix_conversations_user_updated", "conversations", ["user_id", "updated_at"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", JSONB, nullable=False),
        sa.Column("usage", JSONB, nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_user_updated", table_name="conversations")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_index("ix_conversations_kb_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_ingestion_jobs_document_id", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")

    op.drop_index("ix_document_chunks_kb_page", table_name="document_chunks")
    op.drop_index("ix_document_chunks_doc_chunk", table_name="document_chunks")
    op.drop_index("ix_document_chunks_kb_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_documents_kb_status_created", table_name="documents")
    op.drop_index("ix_documents_uploader_id", table_name="documents")
    op.drop_index("ix_documents_kb_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_knowledge_base_members_user_id", table_name="knowledge_base_members")
    op.drop_index("ix_knowledge_base_members_kb_id", table_name="knowledge_base_members")
    op.drop_table("knowledge_base_members")

    op.drop_index("ix_knowledge_bases_owner_id", table_name="knowledge_bases")
    op.drop_table("knowledge_bases")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
