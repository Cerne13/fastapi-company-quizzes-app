from datetime import date
from typing import List

from pydantic import BaseModel


class QuizStatUserRating(BaseModel):
    rating: float


class QuizStatAverageRating(BaseModel):
    quiz_id: int
    total_success_percentage: float
    last_taken: date


class QuizStatAverageRatings(BaseModel):
    total: int
    quizzes: List[QuizStatAverageRating]


class DateRating(BaseModel):
    date: date
    rating: float


class QuizStatDateRating(BaseModel):
    quiz_id: int
    ratings_by_date: List[DateRating]


class QuizStatDateRatings(BaseModel):
    total: int
    quizzes: List[QuizStatDateRating]


class QuizStatLastDate(BaseModel):
    user_id: int
    date: date


class QuizStatUserProgression(BaseModel):
    user_id: int
    data: list[QuizStatDateRating]