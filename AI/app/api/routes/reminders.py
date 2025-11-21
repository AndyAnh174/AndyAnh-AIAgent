from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.security import validate_api_key
from app.db.session import get_session
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.reminder import ReminderService

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.post("", response_model=ReminderResponse)
async def create_reminder(
    payload: ReminderCreate,
    session=Depends(get_session),
    settings=Depends(get_settings),
):
    service = ReminderService(session, settings)
    reminder = await service.create_reminder(payload)
    return ReminderResponse(
        reminder_id=reminder.id,
        next_run_at=reminder.next_run_at,
        cadence=reminder.cadence,
    )

