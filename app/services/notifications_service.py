from datetime import datetime, date

from databases import Database
from fastapi import HTTPException
from sqlalchemy import select, insert, desc, update, delete, func

from app.models.models import Members, Notifications, Users, QuizResults, Quizzes
from app.schemas.notifications import Notification, NotificationList, NotificationCreate
from app.schemas.user_schemas import UserResponse


class NotificationsService:
    def __init__(self, db: Database):
        self.db = db

    # Helper methods
    async def check_if_admin(self, member_id: int) -> None:
        query = select(Members).where(Members.user_id == member_id)
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=403, detail='You must be an admin to do this')

    async def check_user_exists(self, user_id: int):
        check_user_query = select(Users).where(Users.id == user_id)
        existing_user = await self.db.fetch_one(check_user_query)
        if not existing_user:
            raise HTTPException(status_code=404, detail='This user not found')

    # Main methods
    async def get_notifications(self, user_id: int) -> NotificationList:
        await self.check_user_exists(user_id=user_id)

        query = select(Notifications).where(
            Notifications.user_id == user_id
        ).order_by(desc(Notifications.created_at), desc(Notifications.is_read))
        results = await self.db.fetch_all(query)

        if not results:
            raise HTTPException(status_code=404, detail='No notifications found')

        notifications = [
            Notification(
                id=result.__getitem__('id'),
                user_id=result.__getitem__('user_id'),
                message=result.__getitem__('message'),
                is_read=result.__getitem__('is_read'),
                created_at=result.__getitem__('created_at')

            )
            for result in results
        ]

        return NotificationList(
            total=len(results),
            notifications=notifications

        )

    async def mark_notification_read(self, notification_id: int, current_user: UserResponse) -> Notification:
        query = select(Notifications).where(Notifications.id == notification_id)
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='No such notification found')
        if not result.__getitem__('user_id') == current_user.id:
            raise HTTPException(status_code=403, detail='You can modify only your notifications')

        query = update(Notifications).where(Notifications.id == notification_id).values(is_read=True)
        await self.db.execute(query)

        updated_notification = await self.db.fetch_one(select(Notifications).where(Notifications.id == notification_id))
        return Notification(
            id=updated_notification.__getitem__('id'),
            user_id=updated_notification.__getitem__('user_id'),
            message=updated_notification.__getitem__('message'),
            is_read=updated_notification.__getitem__('is_read'),
            created_at=updated_notification.__getitem__('created_at')
        )

    async def get_users_notifications(self, user_id: int, current_user: UserResponse) -> NotificationList:
        await self.check_if_admin(member_id=current_user.id)
        await self.check_user_exists(user_id=user_id)

        result = await self.get_notifications(user_id=user_id)
        return result

    async def create_notification(self, data: NotificationCreate) -> Notification:
        create_query = Notifications.__table__.insert().values(
            user_id=data.user_id,
            message=data.message,
            is_read=False,
            created_at=datetime.utcnow()
        )
        create_result = await self.db.execute(create_query)

        query = select(Notifications).where(Notifications.id == create_result)
        result = await self.db.fetch_one(query)

        return Notification(
            id=result.__getitem__('id'),
            user_id=result.__getitem__('user_id'),
            message=result.__getitem__('message'),
            is_read=result.__getitem__('is_read'),
            created_at=result.__getitem__('created_at')
        )

    async def create_notification_by_admin(self, data: NotificationCreate, current_user: UserResponse) -> Notification:
        await self.check_user_exists(user_id=data.user_id)
        await self.check_if_admin(member_id=current_user.id)

        result = await self.create_notification(data=data)
        return result

    async def delete_notification(self, notification_id: int, current_user: UserResponse) -> None:
        await self.check_if_admin(member_id=current_user.id)

        query = delete(Notifications).where(Notifications.id == notification_id)
        result = await self.db.execute(query)

        if result == 0:
            raise HTTPException(status_code=404, detail='No such notification found')

    async def create_notifications_for_quiz_cooldowns(self) -> None:
        query = select(
            QuizResults.user_id,
            QuizResults.quiz_id,
            func.max(QuizResults.date_of_quiz).label('max_date_of_quiz'),
            Quizzes.cooldown_in_days
        ).select_from(
            QuizResults.__table__.join(
                Quizzes,
                Quizzes.id == QuizResults.quiz_id
            )
        ).group_by(
            QuizResults.user_id,
            QuizResults.quiz_id,
            Quizzes.cooldown_in_days
        )

        results = await self.db.fetch_all(query)

        for result in results:
            max_date_of_quiz = result.__getitem__('max_date_of_quiz')
            cooldown_in_days = result.__getitem__('cooldown_in_days')
            user_id = result.__getitem__('user_id')
            quiz_id = result.__getitem__('quiz_id')

            timedelta_since_last_quiz = date.today() - max_date_of_quiz

            if timedelta_since_last_quiz.days >= cooldown_in_days:
                notification = NotificationCreate(
                    user_id=user_id,
                    message=f"You can take the quiz {quiz_id} again.",
                )
                await self.create_notification(data=notification)

    async def create_notifications_for_quiz_cooldowns_by_admin(self, current_user: UserResponse):
        await self.check_if_admin(member_id=current_user.id)
        await self.create_notifications_for_quiz_cooldowns()