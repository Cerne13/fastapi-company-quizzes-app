from databases import Database
from fastapi import APIRouter, Depends

from app.db.connections import get_db
from app.routes.auth import get_current_user
from app.schemas.quiz_stat_schemas import QuizStatAverageRatings, QuizStatUserRating, QuizStatDateRatings, \
    QuizStatLastDate, QuizStatDateRating, QuizStatUserProgression
from app.schemas.user_schemas import UserResponse
from app.services.auth_service import AuthService
from app.services.quiz_stat_service import QuizStatService

router = APIRouter(
    prefix='/stats',
    tags=['quiz_stats'],
    responses={
        404: {'description': 'Not found'}
    }
)


@router.get('/my_rating/', response_model=QuizStatUserRating)
async def get_my_rating(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuizStatUserRating:
    AuthService.check_user_or_403(user=current_user)
    quiz_stat_service = QuizStatService(db=db)

    result = await quiz_stat_service.get_rating(user=current_user)
    return result


@router.get('/my_average_stats/', response_model=QuizStatAverageRatings)
async def get_my_average_stats(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuizStatAverageRatings:
    AuthService.check_user_or_403(user=current_user)
    quiz_stat_service = QuizStatService(db=db)

    result = await quiz_stat_service.get_success_percentage_for_user(user=current_user)
    return result


@router.get('/my_daily_stats/', response_model=list[QuizStatDateRating])
async def get_my_stats_day_by_day(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> list[QuizStatDateRating]:
    AuthService.check_user_or_403(user=current_user)
    quiz_stat_service = QuizStatService(db=db)

    user_id = current_user.id
    result = await quiz_stat_service.get_success_rate_progression(user_id=user_id)
    return result


@router.get('/daily_stats/{company_id}/{user_id}/', response_model=list[QuizStatDateRating])
async def get_success_rate_progression_for_user(
        company_id: int,
        user_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> list[QuizStatDateRating]:
    AuthService.check_user_or_403(user=current_user)
    quiz_stat_service = QuizStatService(db=db)

    result = await quiz_stat_service.get_success_rate_progression_for_user(
        company_id=company_id,
        user_id=user_id,
        current_user=current_user
    )
    return result


@router.get('/company_daily_stats/{company_id}/', response_model=list[QuizStatUserProgression])
async def get_success_rate_progression_for_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> list[QuizStatUserProgression]:
    AuthService.check_user_or_403(user=current_user)
    quiz_stat_service = QuizStatService(db=db)

    result = await quiz_stat_service.get_success_rate_progression_for_company(company_id=company_id)
    return result


@router.get('/users_daily_stats/{company_id}/', response_model=list[QuizStatLastDate])
async def get_users_daily_stats(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> list[QuizStatLastDate]:
    AuthService.check_user_or_403(user=current_user)
    quiz_stat_service = QuizStatService(db=db)

    result = await quiz_stat_service.get_latest_time_quiz_passed_for_users(
        company_id=company_id,
        current_user=current_user
    )
    return result
