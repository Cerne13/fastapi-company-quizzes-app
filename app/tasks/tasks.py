from databases import Database
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.connections import get_db
from app.services.notifications_service import NotificationsService


async def create_quiz_cooldown_notifications() -> None:
    db: Database = await get_db()
    notification_service = NotificationsService(db=db)
    await notification_service.create_notifications_for_quiz_cooldowns()


scheduler = AsyncIOScheduler(timezone=timezone('Europe/Kiev'))

scheduler.add_job(
    create_quiz_cooldown_notifications,
    "cron",
    hour=0,
    minute=0
)
