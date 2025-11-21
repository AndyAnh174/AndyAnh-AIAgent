from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ReminderCreate(BaseModel):
    entry_id: int | None = None
    email: EmailStr
    subject: str
    body: str
    cadence: str = Field("yearly", description="cron-like alias e.g. daily/weekly/monthly/yearly")
    first_run_at: datetime


class ReminderResponse(BaseModel):
    reminder_id: int
    next_run_at: datetime
    cadence: str

