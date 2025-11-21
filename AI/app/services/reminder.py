from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate
from app.services.email import EmailService
from app.services.scheduler import ReminderScheduler


class ReminderService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.email_service = EmailService(settings)

    async def create_reminder(self, payload: ReminderCreate) -> Reminder:
        reminder = Reminder(
            entry_id=payload.entry_id,
            email=payload.email,
            subject=payload.subject,
            body=payload.body,
            cadence=payload.cadence,
            next_run_at=payload.first_run_at,
        )
        self.session.add(reminder)
        await self.session.flush()

        trigger, trigger_args = self._cadence_to_trigger(payload.cadence)
        ReminderScheduler.add_job(
            self.dispatch_email,
            trigger=trigger,
            id=f"reminder-{reminder.id}",
            next_run_time=payload.first_run_at,
            kwargs={"reminder_id": reminder.id, "settings": self.settings},
            replace_existing=True,
            **trigger_args,
        )

        return reminder

    async def list_active_reminders(self) -> list[Reminder]:
        stmt = select(Reminder).where(Reminder.is_active.is_(True))
        results = await self.session.execute(stmt)
        return list(results.scalars())

    def _cadence_to_trigger(self, cadence: str) -> tuple[str, dict]:
        cadence = cadence.lower()
        mapping = {
            "daily": ("interval", {"days": 1}),
            "weekly": ("interval", {"weeks": 1}),
            "monthly": ("interval", {"weeks": 4}),
            "yearly": ("interval", {"weeks": 52}),
        }
        return mapping.get(cadence, ("interval", {"days": 1}))

    @staticmethod
    async def dispatch_email(reminder_id: int, settings: Settings) -> None:
        from app.db.session import async_session as session_factory

        if session_factory is None:
            raise RuntimeError("Session factory not initialized")
        email_service = EmailService(settings)
        async with session_factory() as session:
            reminder = await session.get(Reminder, reminder_id)
            if not reminder or not reminder.is_active:
                return
            email_service.send_email(reminder.email, reminder.subject, reminder.body)
            reminder.next_run_at = datetime.utcnow()
            await session.commit()

