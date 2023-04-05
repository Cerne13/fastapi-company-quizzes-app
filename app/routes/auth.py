import sys

from databases import Database
from fastapi import APIRouter, Depends

from app.db.connections import get_db
from app.schemas.auth_schemas import Token
from app.schemas.user_schemas import UserResponse, SignInRequest, SignUpRequest
from app.services.auth_service import AuthService, get_current_user_dependency
from app.services.user_service import UserService

sys.path.append('..')

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
    responses={
        401: {'user': 'Not authorized'}
    }
)


@router.post('/login', response_model=Token)
async def login_for_access_token(
        login: SignInRequest,
        db: Database = Depends(get_db)
) -> Token:
    auth_service = AuthService(db=db)
    token = await auth_service.authenticate_user(email=login.user_email, password=login.user_password)
    return token


@router.get('/me/', response_model=UserResponse)
async def get_current_user(
        user: UserResponse = Depends(get_current_user_dependency),
) -> UserResponse:
    return user
