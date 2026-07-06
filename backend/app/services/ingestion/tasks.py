from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import build_document_key, get_storage_backend
from app.core.task_queue import get_task_queue
from app.db.session import async_session_factory
from app.services.document_service import DocumentService
from app.services.embeddings.router import get_embedding_provider
from app.services.fulltext.router import get_fulltext_searcher
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.vector_store.router import get_vector_store

logger = logging.getLogger(__name__)

service = DocumentService()
pipeline = IngestionPipeline()


async def process_document_task(document_id: str, kb_id: str, file_name: str) -> dict:
    """异步处理文档：解析 + 分块 + 向量化 + 索引。

    Args:
        document_id: 文档ID
        kb_id: 知识库ID
        file_name: 文件名

    Returns:
        处理结果统计
    """
    storage = get_storage_backend()
    embedding = get_embedding_provider()
    vector_store = get_vector_store()
    fulltext = get_fulltext_searcher()

    db: AsyncSession = async_session_factory()

    try:
        doc = await service.get_document(db, document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        await service.update_document_status(db, document=doc, parse_status="processing")

        key = build_document_key(doc.sha256, doc.file_name)
        content = storage.load(key)

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_name).suffix) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            parsed = pipeline.process(tmp_path)
            await service.clear_chunks(db, document_id)

            try:
                await vector_store.delete_by_document_id(settings.qdrant_collection, document_id)
            except Exception:
                pass

            try:
                await fulltext.delete_by_document_id(document_id)
            except Exception:
                pass

            chunk_list = []
            for idx, chunk in enumerate(parsed.chunks):
                db_chunk = await service.create_chunk(
                    db,
                    document_id=doc.id,
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
                    "metadata_": db_chunk.metadata_,
                })

                progress = (idx + 1) / max(len(parsed.chunks), 1) * 0.5
                await get_task_queue().update_progress(
                    "", progress, f"分块完成 {idx + 1}/{len(parsed.chunks)}"
                ) if False else None

            from sqlalchemy.orm.attributes import flag_modified
            doc_meta = dict(doc.metadata_ or {})
            doc_meta["chunks"] = len(chunk_list)
            doc_meta.update(parsed.metadata)
            doc.metadata_ = doc_meta
            flag_modified(doc, "metadata_")
            await db.commit()
            await db.refresh(doc)

            if chunk_list:
                await vector_store.ensure_collection(settings.qdrant_collection, settings.embedding_dim)

                texts = [chunk["content"] for chunk in chunk_list]
                embeddings = await embedding.embed_batch(texts)

                vector_batch = []
                fulltext_batch = []
                for idx, chunk in enumerate(chunk_list):
                    emb = embeddings[idx]
                    vector_batch.append({
                        "chunk_id": chunk["chunk_id"],
                        "embedding": emb.embedding,
                        "document_id": document_id,
                        "document_name": file_name,
                        "kb_id": kb_id,
                        "page_start": chunk.get("page_start"),
                        "page_end": chunk.get("page_end"),
                        "metadata": chunk.get("metadata_", {}),
                    })
                    fulltext_batch.append({
                        "chunk_id": chunk["chunk_id"],
                        "document_id": document_id,
                        "document_name": file_name,
                        "kb_id": kb_id,
                        "content": chunk["content"],
                        "page_start": chunk.get("page_start"),
                        "page_end": chunk.get("page_end"),
                        "metadata": chunk.get("metadata_", {}),
                    })

                    progress = 0.5 + (idx + 1) / max(len(chunk_list), 1) * 0.5
                    await get_task_queue().update_progress(
                        "", progress, f"向量化完成 {idx + 1}/{len(chunk_list)}"
                    ) if False else None

                if hasattr(vector_store, "upsert_batch"):
                    await vector_store.upsert_batch(settings.qdrant_collection, vector_batch)
                else:
                    for item in vector_batch:
                        await vector_store.upsert(settings.qdrant_collection, **item)

                if hasattr(fulltext, "index_batch"):
                    try:
                        await fulltext.index_batch(fulltext_batch)
                    except Exception:
                        pass
                else:
                    for item in fulltext_batch:
                        try:
                            await fulltext.index_chunk(**item)
                        except Exception:
                            pass

            parse_status = "completed" if parsed.text or parsed.chunks else "empty"

            await service.update_document_status(db, document=doc, parse_status=parse_status)

            logger.info(f"Document processed: {document_id} ({len(chunk_list)} chunks)")
            return {
                "document_id": document_id,
                "chunks": len(chunk_list),
                "status": parse_status,
            }
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Document processing failed: {document_id}: {e}", exc_info=True)
        try:
            doc = await service.get_document(db, document_id)
            if doc:
                await service.update_document_status(db, document=doc, parse_status="failed")
        except Exception:
            pass
        raise
    finally:
        await db.close()


def register_ingestion_tasks() -> None:
    """注册文档处理任务到任务队列。"""
    tq = get_task_queue()
    tq.register_task("process_document", process_document_task)
    logger.info("Ingestion tasks registered")
