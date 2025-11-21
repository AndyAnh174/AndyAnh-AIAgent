from datetime import datetime
import uuid

from fastapi import Header

from app.services.session_manager import SessionManager


async def get_or_create_session(x_session_id: str | None = Header(default=None)) -> str:
    session_id = x_session_id or str(uuid.uuid4())
    await SessionManager.set_session(session_id, {"last_seen": datetime.utcnow().isoformat()})
    return session_id

