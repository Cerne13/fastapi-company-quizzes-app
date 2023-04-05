from databases import Database
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse, FileResponse

from app.db.connections import get_db
from app.routes.auth import get_current_user
from app.schemas.quiz_schemas import QuizList, QuizResponse, QuizRequest, QuizUpdateRequest, QuestionResponseList, \
    QuestionResponse, QuestionRequest, QuestionUpdate, TakenQuizStats, Rating, QuestionUserResponseList, TestResults, \
    RedisQuizResults, RedisQuizResult
from app.schemas.user_schemas import UserResponse
from app.services.auth_service import AuthService
from app.services.quiz_service import QuizService

router = APIRouter(
    prefix='/quizzes',
    tags=['quizzes'],
    responses={
        404: {'description': 'Not found'}
    }
)


@router.get('/{company_id}', response_model=QuizList)
async def get_all_quizzes_by_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuizList:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_quizzes_by_company(company_id=company_id, user=current_user)
    return result


@router.post('', response_model=QuizResponse)
async def create_quiz_for_company(
        quiz_data: QuizRequest,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuizResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.create_quiz(quiz_data=quiz_data, user=current_user)
    return result


@router.put('/{quiz_id}', response_model=QuizResponse)
async def update_quiz_by_id(
        quiz_id: int,
        quiz_data: QuizUpdateRequest,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuizResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.update_quiz(quiz_id=quiz_id, quiz_data=quiz_data, user=current_user)
    return result


@router.delete('/{company_id}/{quiz_id}', status_code=200)
async def delete_quiz_by_id(
        company_id: int,
        quiz_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    await quiz_service.delete_company_quiz(quiz_id=quiz_id, company_id=company_id, user=current_user)


@router.get('/{quiz_id}/questions', response_model=QuestionResponseList)
async def get_quiz_questions(
        quiz_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuestionResponseList:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_quiz_questions(quiz_id=quiz_id, user=current_user)
    return result


@router.post('/question', response_model=QuestionResponse)
async def create_question(
        quiz_id: int,
        question: QuestionRequest,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuestionResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.create_question(quiz_id=quiz_id, question=question, user=current_user)
    return result


@router.put('/question/update/{question_id}', response_model=QuestionResponse)
async def update_question(
        question_id: int,
        question_data: QuestionUpdate,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuestionResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.update_question(
        question_id=question_id,
        question_data=question_data,
        user=current_user
    )
    return result


@router.delete('/question/delete/{question_id}', status_code=200)
async def delete_question(
        question_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    await quiz_service.delete_question(question_id=question_id, user=current_user)


@router.get('/quiz/{quiz_id}/try', response_model=QuestionUserResponseList)
async def get_questions_list_for_user(
        quiz_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> QuestionUserResponseList:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_question_list_user(quiz_id=quiz_id, user=current_user)
    return result


@router.post('/quiz/{quiz_id}/result/', response_model=TakenQuizStats)
async def save_quiz_result(
        quiz_id: int,
        quiz_answers: TestResults,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> TakenQuizStats:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.save_quiz_result(quiz_id=quiz_id, quiz_answers=quiz_answers, user=current_user)
    return result


@router.get('/quiz_rating/quiz/{quiz_id}/{user_id}/', response_model=Rating)
async def get_quiz_rating_for_user(
        quiz_id: int,
        user_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> Rating:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_rating_by_quiz(quiz_id=quiz_id, user_id=user_id)
    return result


@router.get('/quiz_rating/company/{company_id}/{user_id}/', response_model=Rating)
async def get_rating_for_company(
        company_id: int,
        user_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> Rating:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_rating_by_company(company_id=company_id, user_id=user_id)
    return result


@router.get('/quiz_rating/all/{user_id}/', response_model=Rating)
async def get_overall_rating_for_user(
        user_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> Rating:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_overall_rating(user_id=user_id)
    return result


@router.get('/quiz_rating/json_export/my/', response_model=RedisQuizResults)
async def get_my_quizzes_results(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> JSONResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_my_stats_from_redis(user=current_user)
    return JSONResponse(content=result.json())


@router.get('/quiz_rating/json_export/{company_id}/{user_id}/', response_model=RedisQuizResults)
async def get_quiz_stats_for_user_in_the_company(
        member_id: int,
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> JSONResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_quiz_results_by_user(member_id=member_id, company_id=company_id, user=current_user)
    return JSONResponse(content=result.json())


@router.get('/quiz_rating/json_export_by_company/{company_id}/', response_model=RedisQuizResults)
async def get_quiz_stats_by_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> JSONResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_quiz_results_by_company(company_id=company_id, user=current_user)
    return JSONResponse(content=result.json())


@router.get('/quiz_rating/json_export_by_quiz_id/{quiz_id}/', response_model=RedisQuizResults)
async def get_quiz_stats_by_quiz_in_company(
        quiz_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> JSONResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    result = await quiz_service.get_quiz_results_by_quiz_in_company(quiz_id=quiz_id, user=current_user)
    return JSONResponse(content=result.json())


@router.post('/quiz_rating/write_to_scv/me/', status_code=200)
async def save_my_stats_to_csv(
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> FileResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    await quiz_service.write_my_stats_to_csv(user=current_user)

    file_name = 'my_quiz_results.csv'
    file_path = f"/app/app/utils/{file_name}"
    return FileResponse(file_path, media_type='text/csv', filename=file_name)


@router.post('/quiz_rating/write_to_scv/{company_id}/{user_id}/', status_code=200)
async def save_csv_stats_for_user_in_the_company(
        member_id: int,
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> FileResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    await quiz_service.write_quiz_user_stats_to_csv(member_id=member_id, company_id=company_id, user=current_user)

    file_name = 'user_company_results.csv'
    file_path = f"/app/app/utils/{file_name}"
    return FileResponse(file_path, media_type='text/csv', filename=file_name)


@router.post('/quiz_rating/write_to_csv_by_company/{company_id}/', status_code=200)
async def save_csv_stats_for_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> FileResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    await quiz_service.write_quiz_results_by_company_to_csv(company_id=company_id, user=current_user)

    file_name = 'company_results.csv'
    file_path = f"/app/app/utils/{file_name}"
    return FileResponse(file_path, media_type='text/csv', filename=file_name)


@router.post('/quiz_rating/write_csv_by_quiz_id/{quiz_id}/', status_code=200)
async def get_quiz_stats_by_quiz_in_company(
        quiz_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> FileResponse:
    AuthService.check_user_or_403(user=current_user)
    quiz_service = QuizService(db=db)

    await quiz_service.write_quiz_results_by_quiz_id_to_csv(quiz_id=quiz_id, user=current_user)

    file_name = 'quiz_id_results.csv'
    file_path = f"/app/app/utils/{file_name}"
    return FileResponse(file_path, media_type='text/csv', filename=file_name)
