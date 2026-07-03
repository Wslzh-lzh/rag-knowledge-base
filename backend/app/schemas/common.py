from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageMeta(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20


class APIResponse(BaseModel):
    success: bool = True
    trace_id: str | None = None

