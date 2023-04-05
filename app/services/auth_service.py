import time
from datetime import datetime, timedelta
from typing import Optional

from databases import Database
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select

from app.models.models import Users
from app.schemas.auth_schemas import Token
from app.schemas.user_schemas import UserResponse
from app.services.auth0_service import VerifyToken
from app.db.connections import get_db
from system_config import system_config

token_auth_schema = HTTPBearer()


async def get_current_user_dependency(
        token: str = Depends(token_auth_schema),
        db: Database = Depends(get_db)
) -> UserResponse:
    auth_service = AuthService(db=db)
    user_response = await auth_service.get_current_user(token=token)
    return user_response


class AuthService:
    def __init__(self, db: Database):
        self.db = db
        self.bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        self.secret = system_config.secret_key
        self.algorithm = system_config.algorithm

    @staticmethod
    def get_user_exception():
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={"WWW-Authenticate": "Bearer"}
        )
        return credentials_exception

    @staticmethod
    def check_user_or_403(user):
        if user is None:
            raise HTTPException(status_code=403, detail='For authorized users only')

    def get_password_hash(self, password: str) -> str:
        return self.bcrypt_context.hash(password=password)

    def verify_password(self, plain_pass: str, hashed_pass: str) -> bool:
        return self.bcrypt_context.verify(secret=plain_pass, hash=hashed_pass)

    def create_access_token(
            self,
            email: str,
            expires_delta: Optional[timedelta] = None
    ) -> str:
        encode = {"sub": email}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=20)
        encode.update({"exp": expire})
        return jwt.encode(encode, self.secret, self.algorithm)

    def decode_access_token(self, token: str) -> dict:
        try:
            decoded_token = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return decoded_token if decoded_token["exp"] >= int(time.time()) else None
        except:
            return {}

    def get_email_from_token(self, token: Optional[str] = Depends(HTTPBearer())) -> str:
        jwt_token = token.credentials
        payload = self.decode_access_token(jwt_token)
        email: str = payload.get('sub')
        if not email:
            payload = VerifyToken(jwt_token).verify()
            email = payload.get('email')

        return email

    async def get_user_by_email(self, email: str):
        query = select(Users).where(Users.user_email == email)
        user = await self.db.fetch_one(query)
        return user

    async def authenticate_user(self, email, password) -> Token:
        user = await self.get_user_by_email(email=email)

        if not user or not self.verify_password(
                plain_pass=password,
                hashed_pass=user.__getitem__('user_password')
        ):
            raise self.get_user_exception()

        return Token(
            access_token=self.create_access_token(email=email),
            token_type='Bearer'
        )

    async def get_current_user(
            self, token: Optional[str] = Depends(HTTPBearer())
    ) -> UserResponse:
        try:
            email = self.get_email_from_token(token=token)
            if not email:
                raise self.get_user_exception()

            user = await self.get_user_by_email(email=email)
            if not user:
                raise self.get_user_exception()

            return UserResponse.from_orm(user)

        except JWTError:
            raise self.get_user_exception()
