import json
from datetime import date

from databases import Database
from databases.interfaces import Record
from fastapi import HTTPException
from sqlalchemy import select, delete, update, insert, func, and_

from app.db.connections import redis_conn
from app.models.models import Companies, Members, ActionTypeEnum, Quizzes, QuizQuestions, QuizResults, Users
from app.schemas.notifications import NotificationCreate
from app.schemas.quiz_schemas import QuizResponse, QuizList, QuizRequest, QuizUpdateRequest, QuestionResponseList, \
    QuestionResponse, QuestionRequest, QuestionUpdate, TakenQuizStats, Rating, QuestionUserResponseList, \
    QuestionUserResponse, TestResults, RedisQuizResults
from app.schemas.user_schemas import UserResponse
from app.services.notifications_service import NotificationsService
from app.utils.csv_writer import write_to_csv


class QuizService:
    def __init__(self, db: Database):
        self.db = db

    async def check_company_exists(self, company_id: int) -> None:
        check_company_query = select(Companies).where(Companies.id == company_id)
        existing_company = await self.db.fetch_one(check_company_query)
        if not existing_company:
            raise HTTPException(status_code=404, detail='This company not found')

    async def check_user_exists(self, user_id: int) -> None:
        user_query = select(Users).where(Users.id == user_id)
        result = await self.db.fetch_one(user_query)

        if not result:
            raise HTTPException(status_code=404, detail="This user doesn't exist")

    async def check_quiz_exists(self, quiz_id: int) -> Record:
        query = select(Quizzes).where(Quizzes.id == quiz_id)
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='No such quiz found')

        return result

    async def check_question_exists(self, question_id: int) -> Record:
        query = select(QuizQuestions).where(QuizQuestions.id == question_id)
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='No such question found')

        return result

    async def check_is_admin(self, company_id: int, member_id: int) -> None:
        admin_query = select(Members).where(
            Members.company_id == company_id,
            Members.user_id == member_id,
            Members.status == ActionTypeEnum.IS_ADMIN
        )
        admin = await self.db.fetch_one(admin_query)

        if not admin:
            raise HTTPException(status_code=403, detail="You must be admin in this company to do this")

    async def check_is_member(self, company_id: int, member_id: int) -> None:
        admin_query = select(Members).where(
            Members.company_id == company_id,
            Members.user_id == member_id,
            Members.status.in_([ActionTypeEnum.IS_ADMIN, ActionTypeEnum.IS_ACTIVE])
        )
        member = await self.db.fetch_one(admin_query)

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of the company")

    # Quizzes
    async def get_quizzes_by_company(self, company_id: int, user: UserResponse) -> QuizList:
        await self.check_company_exists(company_id=company_id)
        await self.check_is_admin(company_id=company_id, member_id=user.id)

        query = select(Quizzes).where(Quizzes.company_id == company_id)
        quizzes = await self.db.fetch_all(query)

        return QuizList(
            total=len(quizzes),
            quizzes=[QuizResponse(**dict(item)) for item in quizzes]
        )

    async def create_notifications_for_users(self, quiz_data: QuizRequest, current_user: UserResponse) -> None:
        users_query = select(Members.user_id).where(
            Members.company_id == quiz_data.company_id,
            Members.status.in_([ActionTypeEnum.IS_ACTIVE, ActionTypeEnum.IS_ADMIN])
        )
        users = await self.db.fetch_all(users_query)

        notifications_service = NotificationsService(db=self.db)

        for user in users:
            notification = NotificationCreate(
                user_id=user.__getitem__('user_id'),
                message=f"New quiz '{quiz_data.name}' is available. Take it now!"
            )
            await notifications_service.create_notification(data=notification)

    async def create_quiz(self, quiz_data: QuizRequest, user: UserResponse) -> QuizResponse:
        await self.check_company_exists(company_id=quiz_data.company_id)
        await self.check_is_admin(company_id=quiz_data.company_id, member_id=user.id)

        query = Quizzes.__table__.insert().values(
            company_id=quiz_data.company_id,
            name=quiz_data.name,
            description=quiz_data.description,
            cooldown_in_days=quiz_data.cooldown_in_days
        )

        await self.db.execute(query)

        result_query = select(Quizzes).where(
            Quizzes.company_id == quiz_data.company_id,
            Quizzes.name == quiz_data.name,
            Quizzes.description == quiz_data.description,
        )
        result = await self.db.fetch_one(result_query)

        await self.create_notifications_for_users(quiz_data=quiz_data, current_user=user)

        return result

    async def update_quiz(self, quiz_id: int, quiz_data: QuizUpdateRequest, user: UserResponse) -> QuizResponse:
        quiz_check_result = await self.check_quiz_exists(quiz_id=quiz_id)
        await self.check_company_exists(company_id=quiz_check_result.__getitem__('company_id'))
        await self.check_is_admin(company_id=quiz_check_result.__getitem__('company_id'), member_id=user.id)

        update_data = quiz_data.dict(exclude_unset=True)
        update_query = update(Quizzes).where(Quizzes.id == quiz_id).values(**update_data)
        await self.db.execute(update_query)

        updated_quiz_query = select(Quizzes).where(Quizzes.id == quiz_id)
        updated_quiz = await self.db.fetch_one(updated_quiz_query)
        return updated_quiz

    async def delete_company_quiz(self, quiz_id: int, company_id: int, user: UserResponse) -> None:
        await self.check_company_exists(company_id=company_id)
        await self.check_is_admin(company_id=company_id, member_id=user.id)

        query = delete(Quizzes).where(Quizzes.id == quiz_id)
        result = self.db.execute(query)

        if result == 0:
            raise HTTPException(status_code=404, detail='No such quiz found')

    # Questions
    async def get_quiz_questions(self, quiz_id: int, user: UserResponse) -> QuestionResponseList:
        quiz_check_result = await self.check_quiz_exists(quiz_id=quiz_id)
        await self.check_is_admin(company_id=quiz_check_result.__getitem__('company_id'), member_id=user.id)

        query = select(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
        result = await self.db.fetch_all(query)

        return QuestionResponseList(
            total=len(result),
            question_list=[QuestionResponse(**dict(question)) for question in result]
        )

    async def create_question(self, quiz_id: int, question: QuestionRequest, user: UserResponse) -> QuestionResponse:
        quiz_check_result = await self.check_quiz_exists(quiz_id=quiz_id)
        await self.check_is_admin(company_id=quiz_check_result.__getitem__('company_id'), member_id=user.id)

        query = QuizQuestions.__table__.insert().values(
            quiz_id=question.quiz_id,
            name=question.name,
            answer_variants=question.answer_variants,
            right_answer=question.right_answer
        )
        await self.db.execute(query)

        result_query = select(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
        result = await self.db.fetch_one(result_query)

        return result

    async def check_question_for_modification(self, question_id: int, user_id: int) -> None:
        question_check_result = await self.check_question_exists(question_id)

        quiz_query = select(Quizzes).where(Quizzes.id == question_check_result.__getitem__('quiz_id'))
        quiz_result = await self.db.fetch_one(quiz_query)
        await self.check_is_admin(company_id=quiz_result.__getitem__('company_id'), member_id=user_id)

    async def update_question(
            self,
            question_id: int,
            question_data: QuestionUpdate,
            user: UserResponse
    ) -> QuestionResponse:
        await self.check_question_for_modification(question_id=question_id, user_id=user.id)

        update_data = question_data.dict(exclude_unset=True)
        update_query = update(QuizQuestions).where(QuizQuestions.id == question_id).values(**update_data)
        await self.db.execute(update_query)

        updated_quiz_query = select(QuizQuestions).where(QuizQuestions.id == question_id)
        updated_quiz = await self.db.fetch_one(updated_quiz_query)
        return updated_quiz

    async def delete_question(self, question_id: int, user: UserResponse) -> None:
        await self.check_question_for_modification(question_id=question_id, user_id=user.id)

        query = delete(QuizQuestions).where(QuizQuestions.id == question_id)
        result = await self.db.execute(query)

        if result == 0:
            raise HTTPException(status_code=404, detail='No such question found')

    # Quiz workflow

    async def get_previous_result(self, quiz_id: int, user_id: int) -> Record:
        quiz_results_query = select(QuizResults).where(
            QuizResults.quiz_id == quiz_id,
            QuizResults.user_id == user_id
        ).order_by(QuizResults.id.desc())
        previous_quiz_result = await self.db.fetch_one(query=quiz_results_query)

        return previous_quiz_result

    async def check_quiz_cooldown(self, quiz_id: int, user_id: int) -> None:
        previous_quiz_result = await self.get_previous_result(quiz_id=quiz_id, user_id=user_id)
        quiz_cooldown_query = select(Quizzes.cooldown_in_days).where(Quizzes.id == quiz_id)
        quiz_cooldown_query_result = await self.db.fetch_one(quiz_cooldown_query)
        quiz_cooldown = quiz_cooldown_query_result.__getitem__('cooldown_in_days')

        today = date.today()
        if previous_quiz_result:
            days_since_last_attempt = (today - previous_quiz_result.__getitem__('date_of_quiz')).days

            if days_since_last_attempt < quiz_cooldown:
                raise HTTPException(
                    status_code=403,
                    detail=f'You must wait for {quiz_cooldown} days since last attempt'
                )

    async def get_question_list_user(self, quiz_id, user: UserResponse) -> QuestionUserResponseList:
        quiz_check_result = await self.check_quiz_exists(quiz_id=quiz_id)
        await self.check_is_member(company_id=quiz_check_result.__getitem__('company_id'), member_id=user.id)
        await self.check_quiz_cooldown(quiz_id=quiz_id, user_id=user.id)

        query = select(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
        result = await self.db.fetch_all(query)

        return QuestionUserResponseList(
            total=len(result),
            question_list=[QuestionUserResponse(**dict(question)) for question in result]
        )

    async def get_taken_quiz_statistics(self, quiz_id: int, quiz_answers: TestResults) -> TakenQuizStats:
        query = select(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
        results = await self.db.fetch_all(query)

        quiz_correct_answers = [question.__getitem__('right_answer') for question in results]
        quiz_actual_answers = [answer for answer in quiz_answers.results]

        total = 0
        for item in zip(quiz_correct_answers, quiz_actual_answers):
            if item[0] == item[1]:
                total += 1

        return TakenQuizStats(
            questions_total=len(results),
            right_answers=total,
            taken_on_day=date.today()
        )

    async def redis_set_quiz_data(
            self,
            user_id: int,
            company_id: int,
            quiz_id: int,
            quiz_answers: TestResults
    ) -> None:
        query = select(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
        results = await self.db.fetch_all(query)

        quiz_correct_answers = [question.__getitem__('right_answer') for question in results]
        quiz_actual_answers = [answer for answer in quiz_answers.results]

        if len(quiz_actual_answers) != len(quiz_actual_answers):
            raise HTTPException(status_code=422, detail='Quantity of answers must be equal to that of questions.')

        redis_key = f'{user_id}-{company_id}-{quiz_id}'
        redis_value = []

        for i, question in enumerate(results):
            question_text = question.__getitem__('name')
            user_answer = question.__getitem__('answer_variants')[quiz_actual_answers[i]]
            is_correct = 'correct' if quiz_actual_answers[i] == quiz_correct_answers[i] else 'incorrect'

            quiz_question = {
                'question_text': question_text,
                'user_answer': user_answer,
                'is_correct': is_correct
            }

            redis_value.append(quiz_question)

        redis_conn.set(redis_key, json.dumps(redis_value), ex=3600 * 48)

    async def save_quiz_result(self, quiz_id: int, quiz_answers: TestResults, user: UserResponse) -> TakenQuizStats:
        # Check company
        quiz_company_query = select(Companies).where(
            Companies.id == select(Quizzes.company_id).where(Quizzes.id == quiz_id)
        )
        company = await self.db.fetch_one(query=quiz_company_query)

        await self.check_company_exists(company_id=company.__getitem__('id'))
        await self.check_is_member(company_id=company.__getitem__('id'), member_id=user.id)

        # Check if previous result
        previous_quiz_result = await self.get_previous_result(quiz_id=quiz_id, user_id=user.id)

        if previous_quiz_result:
            await self.check_quiz_cooldown(quiz_id=quiz_id, user_id=user.id)

        # Main logic
        await self.redis_set_quiz_data(
            user_id=user.id,
            company_id=company.__getitem__('id'),
            quiz_id=quiz_id,
            quiz_answers=quiz_answers
        )

        quiz_data = await self.get_taken_quiz_statistics(quiz_id=quiz_id, quiz_answers=quiz_answers)

        summary_questions_total = (
                previous_quiz_result.__getitem__('summary_questions_total') + quiz_data.questions_total
        ) if previous_quiz_result else quiz_data.questions_total

        summary_correct_answers = (
                previous_quiz_result.__getitem__('summary_correct_answers') + quiz_data.right_answers
        ) if previous_quiz_result else quiz_data.right_answers

        quiz_result = QuizResults(
            user_id=user.id,
            company_id=company.__getitem__('id'),
            quiz_id=quiz_id,

            quiz_questions_total=quiz_data.questions_total,
            quiz_correct_answers=quiz_data.right_answers,
            quiz_correct_answers_percentage=round((quiz_data.right_answers / quiz_data.questions_total * 100), 2),

            summary_questions_total=summary_questions_total,
            summary_correct_answers=summary_correct_answers,
            summary_correct_answers_percentage=round((summary_correct_answers / summary_questions_total * 100), 2),

            date_of_quiz=quiz_data.taken_on_day,
        )

        # У меня датабейзы нормально работают с явным определением полей. Поэтому так длинно :(
        query = QuizResults.__table__.insert().values(
            user_id=quiz_result.user_id,
            company_id=quiz_result.company_id,
            quiz_id=quiz_result.quiz_id,

            quiz_questions_total=quiz_result.quiz_questions_total,
            quiz_correct_answers=quiz_result.quiz_correct_answers,
            quiz_correct_answers_percentage=quiz_result.quiz_correct_answers_percentage,

            summary_questions_total=quiz_result.summary_questions_total,
            summary_correct_answers=quiz_result.summary_correct_answers,
            summary_correct_answers_percentage=quiz_result.summary_correct_answers_percentage,

            date_of_quiz=quiz_result.date_of_quiz,
        )
        await self.db.execute(query)

        return TakenQuizStats(
            questions_total=quiz_data.questions_total,
            right_answers=quiz_data.right_answers,
            taken_on_day=quiz_data.taken_on_day
        )

    async def get_rating_by_quiz(self, quiz_id: int, user_id: int) -> Rating:
        await self.check_quiz_exists(quiz_id=quiz_id)
        await self.check_user_exists(user_id=user_id)

        query = select(QuizResults).where(
            QuizResults.quiz_id == quiz_id,
            QuizResults.user_id == user_id
        ).order_by(QuizResults.id.desc())
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='No such quiz found')

        return Rating(
            total_answers=result.__getitem__('summary_questions_total'),
            right_answers=result.__getitem__('summary_correct_answers'),
            rating_percent=result.__getitem__('summary_correct_answers_percentage')
        )

    async def get_rating_by_company(self, company_id, user_id: int) -> Rating:
        await self.check_company_exists(company_id=company_id)
        await self.check_user_exists(user_id=user_id)

        subquery = select(
            QuizResults.quiz_id,
            func.max(QuizResults.id).label("max_id")
        ).where(QuizResults.company_id == company_id).group_by(QuizResults.quiz_id).alias("subquery")

        query = select(QuizResults).select_from(QuizResults.__table__.join(
            subquery,
            and_(
                QuizResults.quiz_id == subquery.c.quiz_id,
                QuizResults.id == subquery.c.max_id
            )
        )).where(QuizResults.user_id == user_id)
        results = await self.db.fetch_all(query)

        if not results:
            raise HTTPException(status_code=404, detail='No such quizzes found')

        total_answers = 0
        right_answers = 0
        rating_percent_sum = 0

        for result in results:
            total_answers += result.__getitem__('summary_questions_total')
            right_answers += result.__getitem__('summary_correct_answers')
            rating_percent_sum += result.__getitem__('summary_correct_answers_percentage')

        return Rating(
            total_answers=total_answers,
            right_answers=right_answers,
            rating_percent=round(rating_percent_sum / len(results), 2)
        )

    async def get_overall_rating(self, user_id: int) -> Rating:
        await self.check_user_exists(user_id=user_id)

        subquery = select(
            QuizResults.quiz_id,
            func.max(QuizResults.id).label("max_id")
        ).group_by(QuizResults.quiz_id).alias("subquery")

        query = select(QuizResults).select_from(QuizResults.__table__.join(
            subquery,
            and_(
                QuizResults.quiz_id == subquery.c.quiz_id,
                QuizResults.id == subquery.c.max_id
            )
        )).where(QuizResults.user_id == user_id)
        results = await self.db.fetch_all(query)

        if not results:
            raise HTTPException(status_code=404, detail='No such quizzes found')

        total_answers = 0
        right_answers = 0
        rating_percent_sum = 0

        for result in results:
            total_answers += result.__getitem__('summary_questions_total')
            right_answers += result.__getitem__('summary_correct_answers')
            rating_percent_sum += result.__getitem__('summary_correct_answers_percentage')

        return Rating(
            total_answers=total_answers,
            right_answers=right_answers,
            rating_percent=round(rating_percent_sum / len(results), 2)
        )

    @staticmethod
    def get_redis_response(pattern: str) -> RedisQuizResults:
        keys = []
        for key in redis_conn.scan_iter(pattern):
            keys.append(key)

        results = []
        for key in keys:
            user_id = key.decode().split("-")[0]
            quiz_id = key.decode().split("-")[-1]
            value = redis_conn.get(key)
            if value:
                quiz_data = {
                    "user_id": user_id,
                    "quiz_id": quiz_id,
                    "questions": json.loads(value)
                }
                results.append(quiz_data)
        return RedisQuizResults(results=results)

    async def get_my_stats_from_redis(self, user: UserResponse) -> RedisQuizResults:
        return self.get_redis_response(pattern=f"{user.id}-*")

    async def get_quiz_results_by_user(self, member_id: int, company_id: int, user: UserResponse) -> RedisQuizResults:
        await self.check_company_exists(company_id=company_id)
        await self.check_is_admin(company_id=company_id, member_id=user.id)
        await self.check_is_member(company_id=company_id, member_id=member_id)

        return self.get_redis_response(pattern=f"{member_id}-{company_id}*")

    async def get_quiz_results_by_company(self, company_id: int, user: UserResponse) -> RedisQuizResults:
        await self.check_company_exists(company_id=company_id)
        await self.check_is_admin(company_id=company_id, member_id=user.id)

        return self.get_redis_response(pattern=f"*-{company_id}-*")

    async def get_quiz_results_by_quiz_in_company(self, quiz_id: int, user: UserResponse) -> RedisQuizResults:
        await self.check_quiz_exists(quiz_id=quiz_id)

        query = select(Quizzes).where(Quizzes.id == quiz_id)
        result = await self.db.fetch_one(query)
        company_id = result.__getitem__('company_id')
        print(company_id)

        await self.check_is_admin(company_id=company_id, member_id=user.id)

        return self.get_redis_response(pattern=f"*-{company_id}-{quiz_id}")

    async def write_my_stats_to_csv(self, user: UserResponse) -> str:
        get_redis_results = self.get_redis_response(pattern=f"{user.id}-*")
        result = write_to_csv(results=get_redis_results, filename='my_quiz_results.csv')
        return result

    async def write_quiz_user_stats_to_csv(self, member_id: int, company_id: int, user: UserResponse) -> str:
        get_redis_results = await self.get_quiz_results_by_user(member_id=member_id, company_id=company_id, user=user)
        result = write_to_csv(results=get_redis_results, filename='user_company_results.csv')
        return result

    async def write_quiz_results_by_company_to_csv(self, company_id: int, user: UserResponse) -> str:
        get_redis_results = await self.get_quiz_results_by_company(company_id=company_id, user=user)
        result = write_to_csv(results=get_redis_results, filename='company_results.csv')
        return result

    async def write_quiz_results_by_quiz_id_to_csv(self, quiz_id: int, user: UserResponse) -> str:
        get_redis_results = await self.get_quiz_results_by_quiz_in_company(quiz_id=quiz_id, user=user)
        result = write_to_csv(results=get_redis_results, filename='quiz_id_results.csv')
        return result
