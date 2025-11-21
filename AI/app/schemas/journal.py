from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MediaUpload(BaseModel):
    type: Literal["image", "video", "pdf"]
    url: str
    caption: str | None = None


class JournalEntryRequest(BaseModel):
    title: str
    content: str
    mood: str | None = Field(default=None, description="Optional user provided mood label")
    tags: list[str] = Field(default_factory=list)
    media: list[MediaUpload] = Field(default_factory=list)


class JournalEntryResponse(BaseModel):
    entry_id: int
    created_at: datetime
    tags: list[str]


class JournalEntrySummary(BaseModel):
    entry_id: int
    title: str
    mood: str | None
    tags: list[str]
    created_at: datetime
    media_count: int


class MediaInfo(BaseModel):
    id: int
    type: str
    url: str
    storage_path: str
    details: dict


class JournalEntryDetail(BaseModel):
    entry_id: int
    title: str
    content: str
    mood: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    media: list[MediaInfo]


class JournalEntryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    mood: str | None = None
    tags: list[str] | None = None
