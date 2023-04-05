from datetime import datetime
from typing import Optional

from databases import Database
from databases.backends.postgres import Record
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select, update, delete

from app.models.models import Users
from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest, UserListResponse, UserResponse


class UserService:
    def __init__(self, db: Database):
        self.db = db
        self.bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    def get_password_hash(self, password: str) -> str:
        return self.bcrypt_context.hash(password)

    @staticmethod
    def validate_password(password: str, repeat_password: str) -> None:
        if len(password) < 4 or not repeat_password or password != repeat_password:
            raise HTTPException(status_code=422, detail='Entered user credentials are invalid')

    async def check_existing_email(self, user: SignUpRequest) -> None:
        query = select(Users).where(Users.user_email == user.user_email)
        existing_user = await self.db.fetch_one(query)

        if existing_user:
            raise HTTPException(status_code=400, detail='User with this email already exists')

    @staticmethod
    def check_user_exists_or_404(user: Record) -> None:
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

    @staticmethod
    def check_ids_for_403(subject_id: int, current_user_id: int) -> None:
        if subject_id != current_user_id:
            raise HTTPException(status_code=403, detail="It's not your account")

    async def get_all_users(self) -> UserListResponse:
        query = select(Users)
        users = await self.db.fetch_all(query)
        total = len(users)

        return UserListResponse(
            total=total,
            users=[UserResponse.from_orm(user) for user in users]
        )

    async def get_user_by_id(self, user_id: int) -> Optional[Users]:
        query = select(Users).where(Users.id == user_id)
        user_model = await self.db.fetch_one(query)
        return user_model if user_model else None

    async def create_new_user(self, create_user: SignUpRequest) -> UserResponse:
        self.validate_password(
            create_user.user_password,
            create_user.user_password_repeat
        )

        await self.check_existing_email(create_user)

        create_user_model = Users(
            user_password=self.get_password_hash(create_user.user_password),
            user_name=create_user.user_name,
            user_email=create_user.user_email,

            is_superuser=Users.is_superuser.default.arg,
            is_active=Users.is_active.default.arg,

            registration_datetime=datetime.now(),
            update_datetime=datetime.now(),
        )

        query = Users.__table__.insert().values(
            user_name=create_user_model.user_name,
            user_email=create_user_model.user_email,
            user_password=create_user_model.user_password,

            is_superuser=create_user_model.is_superuser,
            is_active=create_user_model.is_active,

            registration_datetime=create_user_model.registration_datetime,
            update_datetime=create_user_model.update_datetime,
        )
        await self.db.execute(query)

        user_query = select(Users).where(Users.user_email == create_user.user_email)
        created_user = await self.db.fetch_one(user_query)
        return created_user

    async def update_user(
            self,
            user_id: int,
            update_user: UserUpdateRequest
    ) -> UserResponse:
        user = await self.get_user_by_id(user_id=user_id)
        self.check_user_exists_or_404(user=user)

        update_data = update_user.dict(exclude_unset=True)
        if update_data.get('user_password'):
            update_data['user_password'] = self.get_password_hash(update_data['user_password'])
            print(update_data['user_password'])
        update_data['update_datetime'] = datetime.now()

        update_query = update(Users).where(Users.id == user_id).values(**update_data)
        await self.db.execute(update_query)

        user_query = select(Users).where(Users.id == user_id)
        updated_user = await self.db.fetch_one(user_query)
        return updated_user

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        self.check_user_exists_or_404(user)

        delete_query = delete(Users).where(Users.id == user_id)
        await self.db.execute(delete_query)
