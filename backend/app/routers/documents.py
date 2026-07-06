from __future__ import annotations

import hashlib
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.deps import get_db
from app.core.storage import build_document_key, get_storage_backend
from app.core.task_queue import get_task_queue
from app.schemas.document import DocumentChunkRead, DocumentRead, DocumentStatusRead
from app.services.document_service import DocumentService
from app.services.embeddings.router import get_embedding_provider
from app.services.fulltext.router import get_fulltext_searcher
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.vector_store.router import get_vector_store

service = DocumentService()
pipeline = IngestionPipeline()
_storage = None
_embedding = None
_vector_store = None
_fulltext = None


def _get_storage():
    global _storage
    if _storage is None:
        _storage = get_storage_backend()
    return _storage


def _get_embedding():
    global _embedding
    if _embedding is None:
        _embedding = get_embedding_provider()
    return _embedding


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store


def _get_fulltext():
    global _fulltext
    if _fulltext is None:
        _fulltext = get_fulltext_searcher()
    return _fulltext


def _document_read(doc) -> DocumentRead:
    return DocumentRead(
        id=doc.id,
        kb_id=doc.kb_id,
        uploader_id=doc.uploader_id,
        file_name=doc.file_name,
        file_type=doc.file_type,
        mime_type=doc.mime_type,
        sha256=doc.sha256,
        storage_uri=doc.storage_uri,
        parse_status=doc.parse_status,
        metadata_=doc.metadata_,
    )


def _chunk_read(chunk) -> DocumentChunkRead:
    return DocumentChunkRead(
        id=chunk.id,
        document_id=chunk.document_id,
        kb_id=chunk.kb_id,
        parent_chunk_id=chunk.parent_chunk_id,
        chunk_no=chunk.chunk_no,
        content=chunk.content,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        token_count=chunk.token_count,
        metadata_=chunk.metadata_,
    )


async def _vectorize_chunks(document_id: str, kb_id: str, document_name: str, chunks: list[dict]) -> None:
    embedding = _get_embedding()
    vector_store = _get_vector_store()
    fulltext = _get_fulltext()

    await vector_store.ensure_collection(settings.qdrant_collection, settings.embedding_dim)

    texts = [chunk["content"] for chunk in chunks]
    if not texts:
        return

    embeddings = await embedding.embed_batch(texts)

    for idx, chunk in enumerate(chunks):
        emb = embeddings[idx]
        await vector_store.upsert(
            settings.qdrant_collection,
            chunk_id=chunk["chunk_id"],
            embedding=emb.embedding,
            document_id=document_id,
            document_name=document_name,
            kb_id=kb_id,
            page_start=chunk.get("page_start"),
            page_end=chunk.get("page_end"),
            metadata=chunk.get("metadata_", {}),
        )
        try:
            await fulltext.index_chunk(
                chunk_id=chunk["chunk_id"],
                document_id=document_id,
                document_name=document_name,
                kb_id=kb_id,
                content=chunk["content"],
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                metadata=chunk.get("metadata_", {}),
            )
        except Exception:
            pass


# ============================================================
# Document-scoped endpoints (mounted at /documents)
# ============================================================

router = APIRouter()


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)) -> DocumentRead:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _document_read(doc)


@router.get("/{document_id}/status", response_model=DocumentStatusRead)
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_db)) -> DocumentStatusRead:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    message = "Document parsed" if doc.parse_status in {"completed", "empty"} else "Pipeline pending"
    return DocumentStatusRead(document_id=document_id, parse_status=doc.parse_status, message=message)


@router.post("/{document_id}/reprocess")
async def reprocess_document(document_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    storage = _get_storage()
    key = build_document_key(doc.sha256, doc.file_name)

    if not storage.exists(key):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Source file missing")

    content = storage.load(key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(doc.file_name).suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parsed = pipeline.process(tmp_path)
        await service.clear_chunks(db, document_id)

        vs = _get_vector_store()
        await vs.delete_by_document_id(settings.qdrant_collection, document_id)

        ft = _get_fulltext()
        try:
            await ft.delete_by_document_id(document_id)
        except Exception:
            pass

        chunk_list = []
        for chunk in parsed.chunks:
            db_chunk = await service.create_chunk(
                db,
                document_id=doc.id,
                kb_id=doc.kb_id,
                chunk_no=chunk["chunk_no"],
                content=chunk["content"],
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                token_count=len(chunk["content"].split()),
                metadata_={"source": "reprocess", "char_count": chunk.get("char_count", 0)},
            )
            chunk_list.append({
                "chunk_id": db_chunk.id,
                "content": chunk["content"],
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "metadata_": db_chunk.metadata_,
            })

        await _vectorize_chunks(document_id, doc.kb_id, doc.file_name, chunk_list)
        await service.update_document_status(db, document=doc, parse_status="completed" if parsed.text or parsed.chunks else "empty")
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"document_id": document_id, "status": "reprocessed"}


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
async def list_chunks(document_id: str, db: AsyncSession = Depends(get_db)) -> list[DocumentChunkRead]:
    chunks = await service.list_chunks(db, document_id)
    return [_chunk_read(chunk) for chunk in chunks]


@router.get("/{document_id}/preview")
async def preview_document(document_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    chunks = await service.list_chunks(db, document_id)
    preview_text = ""
    if chunks:
        all_content = "\n\n".join(chunk.content for chunk in chunks[:5])
        preview_text = all_content[:2000]
    return {
        "document_id": document_id,
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "mime_type": doc.mime_type,
        "parse_status": doc.parse_status,
        "total_chunks": len(chunks),
        "preview": preview_text,
        "metadata": doc.metadata_,
    }


@router.patch("/{document_id}/rename", response_model=DocumentRead)
async def rename_document(
    document_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> DocumentRead:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    new_name = body.get("file_name")
    if not new_name or not isinstance(new_name, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_name is required")

    new_name = new_name.strip()
    if len(new_name) == 0 or len(new_name) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_name length must be 1-255")

    updated = await service.rename_document(db, document_id, new_name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _document_read(updated)


@router.put("/{document_id}/content")
async def update_document_content(
    document_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, str]:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.file_type not in {"txt", "md", "markdown", "html", "htm"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit content of {doc.file_type} files",
        )

    content = body.get("content")
    if content is None or not isinstance(content, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="content is required")

    storage = _get_storage()
    old_key = build_document_key(doc.sha256, doc.file_name)

    content_bytes = content.encode("utf-8")
    new_sha256 = hashlib.sha256(content_bytes).hexdigest()
    new_key = build_document_key(new_sha256, doc.file_name)

    storage.save(new_key, content_bytes)

    try:
        storage.delete(old_key)
    except Exception:
        pass

    doc.sha256 = new_sha256
    doc.storage_uri = new_key
    await db.commit()

    vs = _get_vector_store()
    try:
        await vs.delete_by_document_id(settings.qdrant_collection, document_id)
    except Exception:
        pass

    ft = _get_fulltext()
    try:
        await ft.delete_by_document_id(document_id)
    except Exception:
        pass

    if settings.async_process_threshold_mb >= 0 and doc.file_type == "pdf":
        tq = get_task_queue()
        await tq.submit("process_document", document_id, doc.kb_id, doc.file_name)
        await service.update_document_status(db, document=doc, parse_status="pending")
        return {"document_id": document_id, "status": "pending"}

    await service.clear_chunks(db, document_id)
    await service.update_document_status(db, document=doc, parse_status="processing")

    import tempfile
    from pathlib import Path
    from app.services.ingestion.pipeline import IngestionPipeline
    pipeline = IngestionPipeline()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc.file_type}", mode="w", encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parsed = pipeline.process(tmp_path)
        parse_status = "completed" if parsed.text or parsed.chunks else "empty"

        doc_meta = dict(doc.metadata_ or {})
        doc_meta.update(parsed.metadata)
        doc_meta["chunks"] = len(parsed.chunks)
        await service.update_document_metadata(db, document_id, doc_meta)
        await service.update_document_status(db, document=doc, parse_status=parse_status)

        chunk_list = []
        embedding = _get_embedding()
        for chunk in parsed.chunks:
            db_chunk = await service.create_chunk(
                db,
                document_id=document_id,
                kb_id=doc.kb_id,
                chunk_no=chunk["chunk_no"],
                content=chunk["content"],
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                token_count=len(chunk["content"].split()),
                metadata_={"source": "ingestion", "char_count": chunk.get("char_count", 0)},
            )
            chunk_list.append({
                "chunk_id": db_chunk.id,
                "content": chunk["content"],
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
            })

        if chunk_list:
            try:
                await vs.ensure_collection(settings.qdrant_collection, settings.embedding_dim)
                texts = [c["content"] for c in chunk_list]
                embeddings = await embedding.embed_batch(texts)
                vector_batch = []
                fulltext_batch = []
                for idx, c in enumerate(chunk_list):
                    vector_batch.append({
                        "chunk_id": c["chunk_id"],
                        "embedding": embeddings[idx].embedding,
                        "document_id": document_id,
                        "document_name": doc.file_name,
                        "kb_id": doc.kb_id,
                        "page_start": c.get("page_start"),
                        "page_end": c.get("page_end"),
                        "metadata": {"source": "ingestion"},
                    })
                    fulltext_batch.append({
                        "chunk_id": c["chunk_id"],
                        "document_id": document_id,
                        "document_name": doc.file_name,
                        "kb_id": doc.kb_id,
                        "content": c["content"],
                        "page_start": c.get("page_start"),
                        "page_end": c.get("page_end"),
                        "metadata": {"source": "ingestion"},
                    })
                await vs.upsert_many(settings.qdrant_collection, vector_batch)
                try:
                    await ft.upsert_many(fulltext_batch)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Vectorization failed after content update: {e}")

        return {"document_id": document_id, "status": parse_status}
    finally:
        tmp_path.unlink(missing_ok=True)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> None:
    doc = await service.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        vs = _get_vector_store()
        await vs.delete_by_document_id(settings.qdrant_collection, document_id)
    except Exception:
        pass

    try:
        ft = _get_fulltext()
        await ft.delete_by_document_id(document_id)
    except Exception:
        pass

    try:
        storage = _get_storage()
        key = build_document_key(doc.sha256, doc.file_name)
        storage.delete(key)
    except Exception:
        pass

    await service.delete_document(db, document_id)


# ============================================================
# KB-scoped endpoints (mounted at /knowledge-bases/{kb_id})
# ============================================================

kb_documents_router = APIRouter()


def _should_process_async(file_size: int, file_name: str | None) -> bool:
    size_mb = file_size / (1024 * 1024)
    if size_mb >= settings.async_process_threshold_mb:
        return True
    suffix = Path(file_name or "").suffix.lower()
    if suffix == ".pdf":
        return True
    return False


@kb_documents_router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> DocumentRead:
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    storage = _get_storage()
    key = build_document_key(sha256, file.filename)

    if not storage.exists(key):
        storage.save(key, content)
    storage_uri = storage.get_path(key)

    doc_meta = {"size": len(content)}
    is_async = _should_process_async(len(content), file.filename)
    parse_status = "pending" if is_async else "processing"

    doc = await service.create_document(
        db,
        kb_id=kb_id,
        uploader_id=user.id,
        file_name=file.filename or "upload.bin",
        file_type=(file.filename or "bin").rsplit(".", 1)[-1].lower(),
        mime_type=file.content_type or "application/octet-stream",
        sha256=sha256,
        storage_uri=storage_uri,
        metadata=doc_meta,
        parse_status=parse_status,
    )

    if is_async:
        tq = get_task_queue()
        await tq.submit("process_document", doc.id, kb_id, file.filename or "upload.bin")
        return _document_read(doc)

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "").suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parsed = pipeline.process(tmp_path)
        parse_status = "completed" if parsed.text or parsed.chunks else "empty"

        doc_meta.update(parsed.metadata)
        doc_meta["chunks"] = len(parsed.chunks)
        await service.update_document_metadata(db, doc.id, doc_meta)
        await service.update_document_status(db, document=doc, parse_status=parse_status)

        chunk_list = []
        for chunk in parsed.chunks:
            db_chunk = await service.create_chunk(
                db,
                document_id=doc.id,
                kb_id=kb_id,
                chunk_no=chunk["chunk_no"],
                content=chunk["content"],
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                token_count=len(chunk["content"].split()),
                metadata_={"source": "upload", "char_count": chunk.get("char_count", 0)},
            )
            chunk_list.append({
                "chunk_id": db_chunk.id,
                "content": chunk["content"],
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "metadata_": db_chunk.metadata_,
            })

        await _vectorize_chunks(doc.id, kb_id, file.filename or "upload.bin", chunk_list)
    finally:
        tmp_path.unlink(missing_ok=True)

    return _document_read(doc)


@kb_documents_router.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[DocumentRead]:
    docs = await service.list_documents(db, kb_id)
    return [_document_read(doc) for doc in docs]
