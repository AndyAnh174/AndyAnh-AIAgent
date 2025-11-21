import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import close_db_connection, connect_to_db
from app.db.models.reminder import Reminder
from app.services.email import EmailService
from app.services.scheduler import ReminderScheduler
from app.services.session_manager import SessionManager
from sqlalchemy import select

logger = logging.getLogger(__name__)

_shutdown = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info("Received shutdown signal, stopping worker...")
    _shutdown = True


async def check_and_process_reminders(settings, email_service):
    """Check for due reminders and send emails."""
    from app.db import session as db_session
    
    logger.debug("Checking for due reminders...")
    
    if db_session.async_session is None:
        logger.warning("Database session not initialized, skipping reminder check")
        return

    try:
        async with db_session.async_session() as session:
            # Find reminders that are due
            now = datetime.utcnow()
            logger.debug(f"Current UTC time: {now}")
            stmt = select(Reminder).where(
                Reminder.is_active.is_(True),
                Reminder.next_run_at <= now
            )
            results = await session.execute(stmt)
            reminders = list(results.scalars())
            logger.info(f"Found {len(reminders)} due reminder(s)")

            for reminder in reminders:
                try:
                    logger.info(f"Processing reminder {reminder.id}: {reminder.subject}")
                    email_service.send_email(reminder.email, reminder.subject, reminder.body)
                    
                    # Update next run time based on cadence
                    if reminder.cadence == "daily":
                        reminder.next_run_at = datetime.utcnow() + timedelta(days=1)
                    elif reminder.cadence == "weekly":
                        reminder.next_run_at = datetime.utcnow() + timedelta(weeks=1)
                    elif reminder.cadence == "monthly":
                        reminder.next_run_at = datetime.utcnow() + timedelta(weeks=4)
                    elif reminder.cadence == "yearly":
                        reminder.next_run_at = datetime.utcnow() + timedelta(weeks=52)
                    else:
                        # Default to daily
                        reminder.next_run_at = datetime.utcnow() + timedelta(days=1)
                    
                    await session.commit()
                    logger.info(f"Reminder {reminder.id} processed successfully")
                except Exception as exc:
                    logger.error(f"Failed to process reminder {reminder.id}: {exc}", exc_info=True)
                    await session.rollback()
    except Exception as exc:
        logger.error(f"Error checking reminders: {exc}", exc_info=True)


async def main() -> None:
    """Main worker loop."""
    global _shutdown
    
    configure_logging()
    logger.info("Starting reminder worker...")
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    settings = get_settings()
    await connect_to_db(settings.database_url)
    await SessionManager.initialize(settings)
    await ReminderScheduler.initialize(settings)
    
    email_service = EmailService(settings)
    
    logger.info("Reminder worker started, checking reminders every 60 seconds...")
    
    # Main loop: check reminders every 60 seconds
    while not _shutdown:
        try:
            await check_and_process_reminders(settings, email_service)
        except Exception as exc:
            logger.error(f"Error in reminder check loop: {exc}", exc_info=True)
        
        # Wait 60 seconds before next check, but check shutdown flag every second
        for _ in range(60):
            if _shutdown:
                break
            await asyncio.sleep(1)
    
    logger.info("Shutting down reminder worker...")
    await ReminderScheduler.shutdown()
    await SessionManager.shutdown()
    await close_db_connection()
    logger.info("Reminder worker stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        sys.exit(0)

