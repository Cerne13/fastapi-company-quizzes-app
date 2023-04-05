from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class QuizRequest(BaseModel):
    company_id: int
    name: str
    description: str
    cooldown_in_days: int


class QuizUpdateRequest(BaseModel):
    company_id: Optional[int]
    name: Optional[str]
    description: Optional[str]
    cooldown_in_days: Optional[int]


class QuizResponse(BaseModel):
    id: int
    company_id: int
    name: str
    description: str
    cooldown_in_days: int


class QuizList(BaseModel):
    total: int
    quizzes: List[QuizResponse]


class QuestionRequest(BaseModel):
    quiz_id: int
    name: str
    answer_variants: List[str]
    right_answer: int


class QuestionResponse(BaseModel):
    id: int
    quiz_id: int
    name: str
    answer_variants: List[str]
    right_answer: int


class QuestionUpdate(BaseModel):
    quiz_id: Optional[int]
    name: Optional[str]
    answer_variants: Optional[List[str]]
    right_answer: Optional[int]


class QuestionResponseList(BaseModel):
    total: int
    question_list: List[QuestionResponse]


class QuestionUserResponse(BaseModel):
    id: int
    quiz_id: int
    name: str
    answer_variants: List[str]


class QuestionUserResponseList(BaseModel):
    total: int
    question_list: List[QuestionUserResponse]


class TestResults(BaseModel):
    results: List[int]


class TakenQuizStats(BaseModel):
    questions_total: int
    right_answers: int
    taken_on_day: date


class Rating(BaseModel):
    total_answers: int
    right_answers: int
    rating_percent: float



class RedisQuestion(BaseModel):
    question_text: str
    user_answer: str
    is_correct: str


class RedisQuizResult(BaseModel):
    user_id: str
    quiz_id: str
    questions: List[RedisQuestion]


class RedisQuizResults(BaseModel):
    results: List[RedisQuizResult]