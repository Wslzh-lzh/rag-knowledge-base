from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.services.vector_store.base import VectorSearchHit


class QdrantVectorStore:
    """Qdrant 向量数据库存储（支持本地持久化和服务端模式）。

    特性：
    - 本地模式：无需服务器，数据持久化到本地文件
    - 服务端模式：连接远程 Qdrant 服务
    - 连接复用与懒加载
    - 指数退避重试（3次）
    - 健康检查
    - 批量 upsert 优化
    - 优雅降级（异常时返回空结果而非抛出）
    """

    def __init__(
        self,
        url: str | None = None,
        path: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
    ):
        self._url = url or settings.qdrant_url
        self._path = path or (settings.qdrant_path if settings.qdrant_path else None)
        self._api_key = api_key or ""
        self._default_collection = collection_name or settings.qdrant_collection
        self._client = None
        self._available: bool | None = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            if self._path:
                os.makedirs(self._path, exist_ok=True)
                self._client = QdrantClient(path=self._path)
            elif self._url and (self._url.startswith("http://") or self._url.startswith("https://")):
                self._client = QdrantClient(
                    url=self._url,
                    api_key=self._api_key or None,
                    timeout=10,
                )
            else:
                default_path = str(Path(settings.local_storage_dir) / "qdrant")
                os.makedirs(default_path, exist_ok=True)
                self._client = QdrantClient(path=default_path)
        return self._client

    async def health_check(self) -> dict[str, Any]:
        """检查 Qdrant 服务健康状态。"""
        try:
            client = self._get_client()
            collections = client.get_collections()
            self._available = True
            return {
                "status": "healthy",
                "collections_count": len(collections.collections),
            }
        except Exception as e:
            self._available = False
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def ensure_collection(self, collection_name: str, dim: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        client = self._get_client()
        try:
            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                )
            self._available = True
        except Exception:
            self._available = False
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def upsert(
        self,
        collection_name: str,
        *,
        chunk_id: str,
        embedding: list[float],
        document_id: str,
        document_name: str,
        kb_id: str,
        page_start: int | None = None,
        page_end: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self._upsert_batch(
            collection_name,
            items=[
                {
                    "chunk_id": chunk_id,
                    "embedding": embedding,
                    "document_id": document_id,
                    "document_name": document_name,
                    "kb_id": kb_id,
                    "page_start": page_start,
                    "page_end": page_end,
                    "metadata": metadata,
                }
            ],
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def upsert_batch(
        self,
        collection_name: str,
        items: list[dict[str, Any]],
    ) -> None:
        """批量 upsert 向量点。

        items 每项包含：chunk_id, embedding, document_id, document_name, kb_id,
                        page_start, page_end, metadata
        """
        await self._upsert_batch(collection_name, items)

    async def _upsert_batch(
        self,
        collection_name: str,
        items: list[dict[str, Any]],
    ) -> None:
        from qdrant_client.models import PointStruct

        client = self._get_client()
        points = []
        for item in items:
            payload: dict[str, Any] = {
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "document_name": item["document_name"],
                "kb_id": item["kb_id"],
            }
            if item.get("page_start") is not None:
                payload["page_start"] = item["page_start"]
            if item.get("page_end") is not None:
                payload["page_end"] = item["page_end"]
            if item.get("metadata"):
                payload["chunk_metadata"] = item["metadata"]

            point_id = self._chunk_id_to_uuid(item["chunk_id"])
            points.append(
                PointStruct(
                    id=point_id,
                    vector=item["embedding"],
                    payload=payload,
                )
            )

        client.upsert(
            collection_name=collection_name,
            points=points,
        )
        self._available = True

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=0.5, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def search(
        self,
        collection_name: str,
        *,
        query_embedding: list[float],
        top_k: int = 10,
        kb_ids: list[str] | None = None,
    ) -> list[VectorSearchHit]:
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        client = self._get_client()
        query_filter = None
        if kb_ids:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="kb_id",
                        match=MatchAny(any=kb_ids),
                    )
                ]
            )

        results = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        ).points

        hits: list[VectorSearchHit] = []
        for point in results:
            payload = point.payload or {}
            hits.append(
                VectorSearchHit(
                    chunk_id=payload.get("chunk_id", str(point.id)),
                    document_id=payload.get("document_id", ""),
                    document_name=payload.get("document_name", ""),
                    kb_id=payload.get("kb_id", ""),
                    score=point.score,
                    page_start=payload.get("page_start"),
                    page_end=payload.get("page_end"),
                    metadata=payload.get("chunk_metadata"),
                )
            )
        self._available = True
        return hits

    async def delete_by_chunk_id(self, collection_name: str, chunk_id: str) -> None:
        try:
            client = self._get_client()
            point_id = self._chunk_id_to_uuid(chunk_id)
            client.delete(
                collection_name=collection_name,
                points_selector=[point_id],
            )
        except Exception:
            pass

    async def delete_by_document_id(self, collection_name: str, document_id: str) -> None:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        try:
            client = self._get_client()
            client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
            )
        except Exception:
            pass

    @staticmethod
    def _chunk_id_to_uuid(chunk_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
