from databases import Database
from fastapi import HTTPException
from sqlalchemy import select, func, and_, desc

from app.models.models import Companies, Users, Members, ActionTypeEnum, QuizResults
from app.schemas.quiz_stat_schemas import QuizStatAverageRatings, QuizStatAverageRating, QuizStatUserRating, \
    QuizStatDateRatings, QuizStatDateRating, DateRating, QuizStatLastDate, QuizStatUserProgression
from app.schemas.user_schemas import UserResponse


class QuizStatService:
    def __init__(self, db: Database):
        self.db = db

    # Helper methods
    async def check_is_admin(self, company_id: int, member_id: int) -> None:
        admin_query = select(Members).where(
            Members.company_id == company_id,
            Members.user_id == member_id,
            Members.status == ActionTypeEnum.IS_ADMIN
        )
        admin = await self.db.fetch_one(admin_query)

        if not admin:
            raise HTTPException(status_code=403, detail="You must be admin in this company to do this")

    # Main methods
    async def get_rating(self, user: UserResponse) -> QuizStatUserRating:
        subquery = select(
            QuizResults.quiz_id,
            func.max(QuizResults.id).label('max_id')
        ).where(QuizResults.user_id == user.id).group_by(QuizResults.quiz_id).alias('subquery')

        query = select(
            func.avg(QuizResults.summary_correct_answers_percentage)
        ).select_from(
            QuizResults.__table__.join(subquery, and_(
                QuizResults.quiz_id == subquery.c.quiz_id,
                QuizResults.id == subquery.c.max_id
            ))
        )

        result = await self.db.fetch_val(query)
        return QuizStatUserRating(rating=round(result, 2)) if result else QuizStatUserRating(rating=0.0)

    async def get_success_percentage_for_user(self, user: UserResponse) -> QuizStatAverageRatings:
        subquery = select(
            QuizResults.quiz_id,
            func.max(QuizResults.id).label('max_id')
        ).where(QuizResults.user_id == user.id).group_by(QuizResults.quiz_id).alias('subquery')

        query = select(
            QuizResults.quiz_id,
            QuizResults.summary_correct_answers_percentage,
            QuizResults.date_of_quiz.label('last_taken')
        ).select_from(
            QuizResults.__table__.join(subquery, and_(
                QuizResults.quiz_id == subquery.c.quiz_id,
                QuizResults.id == subquery.c.max_id
            ))
        ).group_by(
            QuizResults.quiz_id,
            QuizResults.summary_correct_answers_percentage,
            QuizResults.date_of_quiz
        )

        results = await self.db.fetch_all(query)
        if not results:
            return QuizStatAverageRatings(total=0, quizzes=[])

        quiz_ratings = [
            QuizStatAverageRating(
                quiz_id=row.__getitem__('quiz_id'),
                total_success_percentage=row.__getitem__('summary_correct_answers_percentage'),
                last_taken=row.__getitem__('last_taken')
            ) for row in results
        ]

        return QuizStatAverageRatings(
            total=len(quiz_ratings),
            quizzes=quiz_ratings
        )

    async def get_success_rate_progression(self, user_id: int) -> list[QuizStatDateRating]:
        subquery = select(
            func.max(QuizResults.id).label('max_id'),
            QuizResults.date_of_quiz
        ).where(QuizResults.user_id == user_id).group_by(
            QuizResults.date_of_quiz, QuizResults.quiz_id
        ).alias('subquery')

        query = select(QuizResults).select_from(
            QuizResults.__table__.join(
                subquery,
                and_(
                    QuizResults.id == subquery.c.max_id,
                    QuizResults.date_of_quiz == subquery.c.date_of_quiz
                )
            )
        ).where(QuizResults.user_id == user_id).order_by(
            QuizResults.quiz_id,
            desc(QuizResults.date_of_quiz)
        )
        results = await self.db.fetch_all(query)

        quizzes_dict = {}
        for result in results:
            quiz_id = result.__getitem__('quiz_id')
            rating = result.__getitem__('summary_correct_answers_percentage')
            date = result.__getitem__('date_of_quiz')

            if quiz_id not in quizzes_dict:
                quizzes_dict[quiz_id] = {'quiz_id': quiz_id, 'ratings_by_date': []}

            quizzes_dict[quiz_id]['ratings_by_date'].append(DateRating(date=date, rating=rating))

        quizzes = [QuizStatDateRating(**quiz) for quiz in quizzes_dict.values()]
        return quizzes

    async def get_success_rate_progression_for_user(
            self,
            company_id: int,
            user_id: int,
            current_user: UserResponse
    ) -> list[QuizStatDateRating]:
        await self.check_is_admin(company_id=company_id, member_id=current_user.id)

        result = await self.get_success_rate_progression(user_id=user_id)
        return result

    async def get_success_rate_progression_for_company(self, company_id: int) -> list[QuizStatUserProgression]:
        users_query = select(Users.id).join(Members).where(Members.company_id == company_id)
        users = await self.db.fetch_all(users_query)
        users_ids = [user.__getitem__('id') for user in users]

        success_rate_progressions = []
        for user_id in users_ids:
            success_rate_progression = await self.get_success_rate_progression(user_id)

            success_rate_progressions.append(
                QuizStatUserProgression(user_id=user_id, data=success_rate_progression)
            )

        return success_rate_progressions

    async def get_latest_time_quiz_passed_for_users(
            self,
            company_id: int,
            current_user: UserResponse
    ) -> list[QuizStatLastDate]:
        await self.check_is_admin(company_id=company_id, member_id=current_user.id)

        query = (
            select(
                Users.id,
                func.max(QuizResults.date_of_quiz).label('last_quiz_date')
            )
            .select_from(Users.__table__.join(QuizResults.__table__).join(Companies.__table__))
            .where(Companies.id == company_id)
            .group_by(Users.id)
        )
        rows = await self.db.fetch_all(query=query)

        result = [
            QuizStatLastDate(user_id=row[0], date=row[1].strftime("%Y-%m-%d"))
            for row in rows
        ]
        return result
