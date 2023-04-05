import sys
from typing import Optional

from app.routes.auth import get_current_user

sys.path.append('..')

from fastapi import APIRouter, HTTPException, Depends, status
from databases import Database

from app.schemas.user_schemas import SignUpRequest, UserUpdateRequest, UserResponse, UserListResponse
from app.services.user_service import UserService
from app.db.connections import get_db
from app.services.auth_service import AuthService

router = APIRouter(
    prefix='',
    tags=['users'],
    responses={
        404: {'description': 'Not found'}
    }
)


@router.get('/users/', response_model=UserListResponse)
async def get_all_users(
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> UserListResponse:
    AuthService.check_user_or_403(user=user)

    user_service = UserService(db=db)
    result = await user_service.get_all_users()
    return result


@router.get('/user/{id}/', response_model=UserResponse)
async def get_user_by_id(
        id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> UserResponse:
    AuthService.check_user_or_403(user=user)

    user_service = UserService(db=db)
    user = await user_service.get_user_by_id(user_id=id)
    if user is None:
        raise HTTPException(status_code=404, detail='Invalid id. User not found')

    return user


@router.post('/user/', response_model=UserResponse)
async def create_new_user(
        create_user: SignUpRequest,
        db: Database = Depends(get_db)
) -> UserResponse:
    user_service = UserService(db=db)
    result = await user_service.create_new_user(create_user=create_user)
    return result


@router.put('/user/{id}/', response_model=UserResponse)
async def update_user(
        update_user: UserUpdateRequest,
        id: Optional[int] = None,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> UserResponse:
    if id is None:
        id = user.id

    user_service = UserService(db=db)
    user_service.check_ids_for_403(subject_id=id, current_user_id=user.id)
    result = await user_service.update_user(user_id=user.id, update_user=update_user)
    return result


@router.delete('/user/{id}/')
async def delete_user(
        id: Optional[int] = None,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    if id is None:
        id = user.id

    user_service = UserService(db=db)
    user_service.check_ids_for_403(subject_id=id, current_user_id=user.id)
    await user_service.delete_user(user_id=id)
