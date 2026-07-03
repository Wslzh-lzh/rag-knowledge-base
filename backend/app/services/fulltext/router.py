from __future__ import annotations

import logging

from app.core.config import settings
from app.services.fulltext.base import FulltextSearcher
from app.services.fulltext.opensearch_searcher import OpenSearchFulltextSearcher
from app.services.fulltext.postgresql_searcher import PostgreSQLFulltextSearcher

logger = logging.getLogger(__name__)

_fulltext_searcher: FulltextSearcher | None = None


def get_fulltext_searcher() -> FulltextSearcher:
    global _fulltext_searcher
    if _fulltext_searcher is None:
        backend = settings.fulltext_search_backend
        if backend == "opensearch":
            try:
                _fulltext_searcher = OpenSearchFulltextSearcher()
                logger.info("Using OpenSearch fulltext searcher: %s", settings.opensearch_url)
            except Exception as e:
                logger.warning("OpenSearch connection failed, falling back to PostgreSQL: %s", e)
                _fulltext_searcher = PostgreSQLFulltextSearcher()
        else:
            _fulltext_searcher = PostgreSQLFulltextSearcher()
            logger.info("Using PostgreSQL fulltext searcher")
    return _fulltext_searcher
