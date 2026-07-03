from __future__ import annotations

from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.services.fulltext.base import FulltextSearchHit


class OpenSearchFulltextSearcher:
    """基于 OpenSearch 的全文检索实现（生产环境调优版）。

    生产环境特性：
    - 连接池复用（RequestsHttpConnection）
    - 指数退避重试（3次写入，2次查询）
    - 健康检查
    - 批量索引（Bulk API）
    - IK 分词器自动检测与降级
    - 优雅降级
    """

    def __init__(
        self,
        url: str | None = None,
        index_name: str | None = None,
        username: str | None = None,
        password: str | None = None,
        use_ik_analyzer: bool | None = None,
    ) -> None:
        self._url = url or settings.opensearch_url
        self._index_name = index_name or settings.opensearch_index
        self._username = username or getattr(settings, "opensearch_username", None)
        self._password = password or getattr(settings, "opensearch_password", None)
        self._use_ik_analyzer = use_ik_analyzer if use_ik_analyzer is not None else settings.opensearch_use_ik_analyzer
        self._client = None
        self._available: bool | None = None
        self._index_ensured = False
        self._ik_available: bool | None = None

    def _get_client(self):
        if self._client is None:
            from opensearchpy import OpenSearch, RequestsHttpConnection

            kwargs = {
                "hosts": [self._url],
                "connection_class": RequestsHttpConnection,
                "timeout": 10,
                "max_retries": 3,
                "retry_on_timeout": True,
                "pool_maxsize": 10,
            }
            if self._username and self._password:
                kwargs["http_auth"] = (self._username, self._password)
            kwargs["use_ssl"] = self._url.startswith("https")
            kwargs["verify_certs"] = False
            kwargs["ssl_show_warn"] = False

            self._client = OpenSearch(**kwargs)
        return self._client

    async def _check_ik_available(self) -> bool:
        if self._ik_available is not None:
            return self._ik_available
        if not self._use_ik_analyzer:
            self._ik_available = False
            return False

        try:
            client = self._get_client()
            resp = client.cat.plugins(format="json")
            for plugin in resp:
                if plugin.get("component") == "analysis-ik" or "ik" in plugin.get("component", "").lower():
                    self._ik_available = True
                    return True
            self._ik_available = False
        except Exception:
            self._ik_available = False
        return self._ik_available

    async def health_check(self) -> dict[str, Any]:
        """检查 OpenSearch 服务健康状态。"""
        try:
            client = self._get_client()
            info = client.info()
            cluster_health = client.cluster.health()
            ik_available = await self._check_ik_available()
            self._available = True
            return {
                "status": "healthy",
                "version": info.get("version", {}).get("number", ""),
                "cluster_status": cluster_health.get("status", ""),
                "index": self._index_name,
                "ik_analyzer": ik_available,
            }
        except Exception as e:
            self._available = False
            return {
                "status": "unhealthy",
                "error": str(e),
                "index": self._index_name,
            }

    async def _ensure_index(self) -> None:
        if self._index_ensured:
            return
        client = self._get_client()
        if not client.indices.exists(index=self._index_name):
            ik_available = await self._check_ik_available()

            if ik_available:
                mapping = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "1s",
                        "analysis": {
                            "analyzer": {
                                "ik_smart": {
                                    "type": "ik_smart",
                                },
                                "ik_max_word": {
                                    "type": "ik_max_word",
                                },
                            }
                        },
                    },
                    "mappings": {
                        "properties": {
                            "chunk_id": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "document_name": {"type": "keyword"},
                            "kb_id": {"type": "keyword"},
                            "content": {
                                "type": "text",
                                "analyzer": "ik_max_word",
                                "search_analyzer": "ik_smart",
                            },
                            "page_start": {"type": "integer"},
                            "page_end": {"type": "integer"},
                        }
                    },
                }
            else:
                mapping = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "1s",
                        "analysis": {
                            "analyzer": {
                                "default": {
                                    "type": "standard",
                                    "stopwords": "_none_",
                                }
                            }
                        },
                    },
                    "mappings": {
                        "properties": {
                            "chunk_id": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "document_name": {"type": "keyword"},
                            "kb_id": {"type": "keyword"},
                            "content": {
                                "type": "text",
                                "analyzer": "default",
                            },
                            "page_start": {"type": "integer"},
                            "page_end": {"type": "integer"},
                        }
                    },
                }

            try:
                client.indices.create(index=self._index_name, body=mapping)
            except Exception:
                basic_mapping = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "1s",
                    },
                    "mappings": {
                        "properties": {
                            "chunk_id": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "document_name": {"type": "keyword"},
                            "kb_id": {"type": "keyword"},
                            "content": {"type": "text"},
                            "page_start": {"type": "integer"},
                            "page_end": {"type": "integer"},
                        }
                    },
                }
                client.indices.create(index=self._index_name, body=basic_mapping)
        self._index_ensured = True
        self._available = True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def index_chunk(
        self,
        *,
        chunk_id: str,
        document_id: str,
        document_name: str,
        kb_id: str,
        content: str,
        page_start: int | None = None,
        page_end: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self._ensure_index()
        client = self._get_client()
        doc = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "document_name": document_name,
            "kb_id": kb_id,
            "content": content,
        }
        if page_start is not None:
            doc["page_start"] = page_start
        if page_end is not None:
            doc["page_end"] = page_end

        client.index(
            index=self._index_name,
            id=chunk_id,
            body=doc,
            refresh="wait_for",
        )
        self._available = True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def index_batch(
        self,
        items: list[dict[str, Any]],
    ) -> None:
        """批量索引文档。

        items 每项包含：chunk_id, document_id, document_name, kb_id, content,
                        page_start, page_end, metadata
        """
        from opensearchpy import helpers

        await self._ensure_index()
        client = self._get_client()

        actions = []
        for item in items:
            doc = {
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "document_name": item["document_name"],
                "kb_id": item["kb_id"],
                "content": item["content"],
            }
            if item.get("page_start") is not None:
                doc["page_start"] = item["page_start"]
            if item.get("page_end") is not None:
                doc["page_end"] = item["page_end"]

            actions.append(
                {
                    "_index": self._index_name,
                    "_id": item["chunk_id"],
                    "_source": doc,
                }
            )

        helpers.bulk(client, actions, refresh="wait_for")
        self._available = True

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=0.5, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def search(
        self,
        query: str,
        *,
        kb_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FulltextSearchHit]:
        await self._ensure_index()
        client = self._get_client()

        ik_available = await self._check_ik_available()

        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["content^3", "document_name"],
                    "type": "best_fields",
                }
            }
        ]

        filter_clauses = []
        if kb_ids:
            filter_clauses.append({"terms": {"kb_id": kb_ids}})

        body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                }
            },
            "size": top_k,
            "highlight": {
                "fields": {
                    "content": {
                        "pre_tags": ["<em>"],
                        "post_tags": ["</em>"],
                        "fragment_size": 150,
                        "number_of_fragments": 1,
                    }
                }
            },
            "track_scores": True,
        }
        if filter_clauses:
            body["query"]["bool"]["filter"] = filter_clauses

        resp = client.search(index=self._index_name, body=body, request_timeout=15)

        hits: list[FulltextSearchHit] = []
        for hit in resp.get("hits", {}).get("hits", []):
            source = hit["_source"]
            highlight = hit.get("highlight", {}).get("content", [])
            highlight_text = highlight[0] if highlight else None

            hits.append(
                FulltextSearchHit(
                    chunk_id=source.get("chunk_id", hit["_id"]),
                    document_id=source.get("document_id", ""),
                    document_name=source.get("document_name", ""),
                    kb_id=source.get("kb_id", ""),
                    score=hit.get("_score", 0.0),
                    page_start=source.get("page_start"),
                    page_end=source.get("page_end"),
                    content=source.get("content", ""),
                    highlight=highlight_text,
                )
            )
        self._available = True
        return hits

    async def delete_by_chunk_id(self, chunk_id: str) -> None:
        try:
            await self._ensure_index()
            client = self._get_client()
            client.delete(index=self._index_name, id=chunk_id, refresh="wait_for")
        except Exception:
            pass

    async def delete_by_document_id(self, document_id: str) -> None:
        try:
            await self._ensure_index()
            client = self._get_client()
            client.delete_by_query(
                index=self._index_name,
                body={"query": {"term": {"document_id": document_id}}},
                refresh=True,
            )
        except Exception:
            pass
