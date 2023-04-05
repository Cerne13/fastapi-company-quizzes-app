from datetime import datetime
from typing import List

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: int
    message: str


class Notification(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    total: int
    notifications: List[Notification]
