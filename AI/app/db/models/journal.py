from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, int_pk


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int_pk]
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    mood: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sentiment_score: Mapped[float | None]
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    media_assets: Mapped[list["MediaAsset"]] = relationship("MediaAsset", back_populates="entry")
    reminders: Mapped[list["Reminder"]] = relationship("Reminder", back_populates="entry")
    analysis_notes: Mapped[list["AnalysisMetadata"]] = relationship("AnalysisMetadata", back_populates="entry")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int_pk]
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"))
    asset_type: Mapped[str] = mapped_column(String(32))
    storage_path: Mapped[str] = mapped_column(String(512))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    entry: Mapped[JournalEntry] = relationship("JournalEntry", back_populates="media_assets")


class AnalysisMetadata(Base):
    __tablename__ = "analysis_metadata"

    id: Mapped[int_pk]
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(64), default="journal")
    custom_notes: Mapped[str | None]
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)

    entry: Mapped[JournalEntry] = relationship("JournalEntry", back_populates="analysis_notes")

