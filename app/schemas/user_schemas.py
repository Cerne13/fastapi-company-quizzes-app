from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class SignInRequest(BaseModel):
    user_email: EmailStr
    user_password: str


class SignUpRequest(BaseModel):
    user_name: str
    user_email: EmailStr
    user_password: str
    user_password_repeat: str


class UserUpdateRequest(BaseModel):
    user_name: Optional[str]
    user_password: Optional[str]
    description: Optional[str]


class AdminUserUpdateRequest(BaseModel):
    user_name: Optional[str]
    user_password: Optional[str]
    is_superuser: Optional[bool]
    is_active: Optional[bool]
    description: Optional[str]


class UserResponse(BaseModel):
    id: int
    user_name: str
    user_email: EmailStr

    is_superuser: bool
    is_active: bool

    description: Optional[str]

    registration_datetime: datetime
    update_datetime: datetime

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]
