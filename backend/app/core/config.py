from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "RAG Knowledge Base"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "local"

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_json_format: bool = Field(default=False, validation_alias="LOG_JSON_FORMAT")

    cors_origins: list[str] = Field(default_factory=lambda: ["*"], validation_alias="CORS_ORIGINS")
    enable_rate_limit: bool = Field(default=False, validation_alias="ENABLE_RATE_LIMIT")
    rate_limit_per_minute: int = Field(default=60, validation_alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, validation_alias="RATE_LIMIT_PER_HOUR")

    max_upload_size_mb: int = Field(default=50, validation_alias="MAX_UPLOAD_SIZE_MB")
    async_process_threshold_mb: int = Field(default=10, validation_alias="ASYNC_PROCESS_THRESHOLD_MB")
    pdf_parser_backend: str = Field(default="auto", validation_alias="PDF_PARSER_BACKEND")
    pdf_enable_toc: bool = Field(default=True, validation_alias="PDF_ENABLE_TOC")
    pdf_enable_table_extract: bool = Field(default=False, validation_alias="PDF_ENABLE_TABLE_EXTRACT")

    database_url: str = Field(
        default="postgresql+asyncpg://rag:rag@localhost:5432/rag_kb",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    opensearch_url: str = Field(default="http://localhost:9200", validation_alias="OPENSEARCH_URL")

    object_storage_url: str = Field(default="http://localhost:9000", validation_alias="OBJECT_STORAGE_URL")
    object_storage_access_key: str = Field(default="minio", validation_alias="OBJECT_STORAGE_ACCESS_KEY")
    object_storage_secret_key: str = Field(default="minio12345", validation_alias="OBJECT_STORAGE_SECRET_KEY")
    object_storage_bucket: str = Field(default="rag-documents", validation_alias="OBJECT_STORAGE_BUCKET")
    object_storage_use_path_style: bool = Field(default=True, validation_alias="OBJECT_STORAGE_USE_PATH_STYLE")

    storage_backend: str = Field(default="local", validation_alias="STORAGE_BACKEND")
    local_storage_dir: str = Field(default="work/storage", validation_alias="LOCAL_STORAGE_DIR")

    vector_store_backend: str = Field(default="memory", validation_alias="VECTOR_STORE_BACKEND")
    qdrant_collection: str = Field(default="rag_chunks", validation_alias="QDRANT_COLLECTION")
    qdrant_path: str = Field(default="", validation_alias="QDRANT_PATH")
    fulltext_search_backend: str = Field(default="postgresql", validation_alias="FULLTEXT_SEARCH_BACKEND")
    opensearch_index: str = Field(default="rag_chunks", validation_alias="OPENSEARCH_INDEX")
    opensearch_use_ik_analyzer: bool = Field(default=True, validation_alias="OPENSEARCH_USE_IK_ANALYZER")

    jwt_secret_key: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 30
    bootstrap_admin_email: str = Field(default="admin@example.com", validation_alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_password: str = Field(default="ChangeMe123!", validation_alias="BOOTSTRAP_ADMIN_PASSWORD")

    default_embedding_model: str = "BGE-M3"
    default_embedding_provider: str = Field(default="mock", validation_alias="DEFAULT_EMBEDDING_PROVIDER")
    embedding_dim: int = Field(default=1024, validation_alias="EMBEDDING_DIM")
    default_reranker_model: str = "gte-rerank-v2"
    default_reranker_provider: str = Field(default="mock", validation_alias="DEFAULT_RERANKER_PROVIDER")
    default_llm_provider: str = Field(default="echo", validation_alias="DEFAULT_LLM_PROVIDER")
    default_llm_model: str = Field(default="qwen-turbo", validation_alias="LLM_MODEL")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", validation_alias="LLM_BASE_URL")

    dashscope_api_key: str = Field(default="", validation_alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias="DASHSCOPE_BASE_URL",
    )
    dashscope_llm_model: str = Field(default="qwen-turbo", validation_alias="DASHSCOPE_LLM_MODEL")
    dashscope_embedding_model: str = Field(default="text-embedding-v3", validation_alias="DASHSCOPE_EMBEDDING_MODEL")
    dashscope_reranker_model: str = Field(default="gte-rerank-v2", validation_alias="DASHSCOPE_RERANKER_MODEL")

    embedding_api_key: str = Field(default="", validation_alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(default="", validation_alias="EMBEDDING_BASE_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
