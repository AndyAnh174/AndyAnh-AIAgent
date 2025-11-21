from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AnalysisMetadata, JournalEntry


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self, limit: int = 200) -> dict[str, Any]:
        result = await self.session.execute(
            select(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit)
        )
        entries: list[JournalEntry] = result.scalars().all()

        if not entries:
            return {
                "mood_trend": [],
                "mood_frequency": {},
                "top_topics": [],
                "insights": [],
                "last_updated": datetime.utcnow().isoformat(),
            }

        mood_trend: list[dict[str, Any]] = []
        mood_counter: Counter[str] = Counter()
        topic_counter: Counter[str] = Counter()

        for entry in reversed(entries):
            if entry.mood:
                mood_trend.append(
                    {
                        "date": entry.created_at.isoformat(),
                        "mood": entry.mood,
                        "score": entry.sentiment_score,
                    }
                )
                mood_counter.update([entry.mood])
            if entry.tags:
                topic_counter.update(entry.tags)

        metadata_result = await self.session.execute(select(AnalysisMetadata))
        for extra in metadata_result.scalars().all():
            notes_topics = extra.metrics.get("topics") if extra.metrics else None
            if isinstance(notes_topics, list):
                topic_counter.update(notes_topics)

        top_topics = [
            {"topic": topic, "count": count}
            for topic, count in topic_counter.most_common(8)
        ]

        insights = self._build_insights(entries, mood_counter, topic_counter)

        return {
            "mood_trend": mood_trend[-60:],  # most recent 60 points
            "mood_frequency": dict(mood_counter),
            "top_topics": top_topics,
            "insights": insights,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _build_insights(
        self,
        entries: list[JournalEntry],
        mood_counter: Counter[str],
        topic_counter: Counter[str],
    ) -> list[dict[str, str]]:
        insights: list[dict[str, str]] = []

        if mood_counter:
            top_mood, count = mood_counter.most_common(1)[0]
            insights.append(
                {
                    "title": "Dominant mood",
                    "description": f"Bạn nhắc đến trạng thái '{top_mood}' {count} lần gần đây.",
                }
            )

        if topic_counter:
            topic, count = topic_counter.most_common(1)[0]
            insights.append(
                {
                    "title": "Recurring topic",
                    "description": f"Chủ đề '{topic}' xuất hiện {count} lần trong nhật ký/chat.",
                }
            )

        if entries:
            latest = entries[0]
            insights.append(
                {
                    "title": "Most recent entry",
                    "description": f"Entry gần nhất lúc {latest.created_at.strftime('%d/%m %H:%M')} với mood '{latest.mood or 'n/a'}'.",
                }
            )

        return insights

