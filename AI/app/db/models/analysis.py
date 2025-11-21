from datetime import datetime

from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, int_pk


class MoodTrend(Base):
    __tablename__ = "analysis_mood_trends"

    id: Mapped[int_pk]
    date: Mapped[datetime]
    mood: Mapped[str] = mapped_column(String(64))
    score: Mapped[float]


class TopicStat(Base):
    __tablename__ = "analysis_topic_stats"

    id: Mapped[int_pk]
    topic: Mapped[str] = mapped_column(String(128))
    frequency: Mapped[int] = mapped_column(Integer)
    last_seen: Mapped[datetime]

