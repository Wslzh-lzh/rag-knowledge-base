from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DocumentRead(ORMModel):
    id: str
    kb_id: str
    uploader_id: str
    file_name: str
    file_type: str
    mime_type: str
    sha256: str
    storage_uri: str
    parse_status: str
    metadata_: dict = Field(default_factory=dict, alias="metadata", serialization_alias="metadata")


class DocumentChunkRead(ORMModel):
    id: str
    document_id: str
    kb_id: str
    parent_chunk_id: str | None = None
    chunk_no: int
    content: str
    page_start: int | None = None
    page_end: int | None = None
    token_count: int
    metadata_: dict = Field(default_factory=dict, alias="metadata", serialization_alias="metadata")


class DocumentStatusRead(BaseModel):
    document_id: str
    parse_status: str
    message: str | None = None
