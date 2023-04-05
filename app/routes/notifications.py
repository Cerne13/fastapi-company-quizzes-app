from databases import Database
from fastapi import APIRouter, Depends

from app.db.connections import get_db
from app.routes.auth import get_current_user
from app.schemas.notifications import NotificationList, Notification, NotificationCreate
from app.schemas.user_schemas import UserResponse
from app.services.auth_service import AuthService
from app.services.notifications_service import NotificationsService

router = APIRouter(
    prefix='/notifications',
    tags=['notifications'],
    responses={
        404: {'description': 'Not found'}
    }
)


# For users
@router.get('/me/', response_model=NotificationList)
async def get_my_notifications(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> NotificationList:
    AuthService.check_user_or_403(user=current_user)
    notifications_service = NotificationsService(db=db)

    result = await notifications_service.get_notifications(user_id=current_user.id)
    return result


@router.post('/me/{notification_id}/')
async def mark_my_notification_read(
        notification_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> Notification:
    AuthService.check_user_or_403(user=current_user)
    notifications_service = NotificationsService(db=db)

    result = await notifications_service.mark_notification_read(
        notification_id=notification_id,
        current_user=current_user
    )
    return result


# For admins
@router.get('/{user_id}/', response_model=NotificationList)
async def get_user_notifications(
        user_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> NotificationList:
    AuthService.check_user_or_403(user=current_user)
    notifications_service = NotificationsService(db=db)

    result = await notifications_service.get_users_notifications(user_id=user_id, current_user=current_user)
    return result


@router.post('/create_new/', response_model=Notification)
async def create_notification(
        data: NotificationCreate,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> Notification:
    AuthService.check_user_or_403(user=current_user)
    notifications_service = NotificationsService(db=db)

    result = await notifications_service.create_notification_by_admin(data=data, current_user=current_user)
    return result


@router.delete('/{notification_id}/', status_code=200)
async def delete_notification(
        notification_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    notifications_service = NotificationsService(db=db)

    await notifications_service.delete_notification(notification_id=notification_id, current_user=current_user)


@router.post('/create_notifications_for_quiz_cooldowns_manually')
async def create_quiz_cooldowns_notifications(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    notifications_service = NotificationsService(db=db)
    await notifications_service.create_notifications_for_quiz_cooldowns_by_admin(current_user=current_user)