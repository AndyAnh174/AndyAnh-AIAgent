import json
from typing import Any

import redis.asyncio as redis

from app.core.config import Settings


class SessionManager:
    _client: redis.Redis | None = None
    _ttl: int = 0
    _memory_store: dict[str, dict[str, Any]] = {}

    @classmethod
    async def initialize(cls, settings: Settings) -> None:
        if cls._client:
            return
        try:
            cls._client = redis.from_url(settings.redis_url, decode_responses=True)
            await cls._client.ping()
        except Exception:
            cls._client = None
        cls._ttl = settings.session_ttl_seconds

    @classmethod
    async def shutdown(cls) -> None:
        if cls._client:
            await cls._client.close()
        cls._client = None

    @classmethod
    async def get_session(cls, session_id: str) -> dict[str, Any] | None:
        if cls._client is not None:
            data = await cls._client.get(session_id)
            return json.loads(data) if data else None
        return cls._memory_store.get(session_id)

    @classmethod
    async def set_session(cls, session_id: str, payload: dict[str, Any]) -> None:
        if cls._client is not None:
            await cls._client.set(session_id, json.dumps(payload), ex=cls._ttl)
        else:
            cls._memory_store[session_id] = payload

