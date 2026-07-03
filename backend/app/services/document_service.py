from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk, IngestionJob


class DocumentService:
    async def create_document(
        self,
        db: AsyncSession,
        *,
        kb_id: str,
        uploader_id: str,
        file_name: str,
        file_type: str,
        mime_type: str,
        sha256: str,
        storage_uri: str,
        metadata: dict,
        parse_status: str = "pending",
    ) -> Document:
        doc = Document(
            kb_id=kb_id,
            uploader_id=uploader_id,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            sha256=sha256,
            storage_uri=storage_uri,
            parse_status=parse_status,
            metadata_=metadata,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    async def list_documents(self, db: AsyncSession, kb_id: str) -> list[Document]:
        result = await db.execute(select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc()))
        return list(result.scalars().all())

    async def create_chunk(self, db: AsyncSession, **payload) -> DocumentChunk:
        if "metadata" in payload and "metadata_" not in payload:
            payload["metadata_"] = payload.pop("metadata")
        chunk = DocumentChunk(**payload)
        db.add(chunk)
        await db.commit()
        await db.refresh(chunk)
        return chunk

    async def enqueue_job(self, db: AsyncSession, *, document_id: str, payload: dict) -> IngestionJob:
        job = IngestionJob(document_id=document_id, payload=payload)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def get_document(self, db: AsyncSession, document_id: str) -> Document | None:
        return await db.get(Document, document_id)

    async def list_chunks(self, db: AsyncSession, document_id: str) -> list[DocumentChunk]:
        result = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_no.asc()))
        return list(result.scalars().all())

    async def update_document_status(
        self,
        db: AsyncSession,
        *,
        document: Document,
        parse_status: str,
    ) -> Document:
        document.parse_status = parse_status
        await db.commit()
        await db.refresh(document)
        return document

    async def clear_chunks(self, db: AsyncSession, document_id: str) -> None:
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        await db.commit()
