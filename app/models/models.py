from datetime import datetime, date
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, ARRAY, Date, Float
from sqlalchemy import Enum as EnumDB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

Base = declarative_base()


class ActionTypeEnum(str, Enum):
    INVITED = 'invited'
    APPLYING = 'applying'
    IS_ACTIVE = 'is_active'
    DEACTIVATED = 'deactivated'
    IS_ADMIN = 'is_admin'


class Members(Base):
    __tablename__ = 'members'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey('users.id'))
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'))
    status = Column(EnumDB(ActionTypeEnum), nullable=False, default=ActionTypeEnum.DEACTIVATED)

    company = relationship("Companies", backref="members")
    user = relationship("Users", backref="memberships")

    UniqueConstraint(user_id, company_id)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    user_name = Column(String, index=True, nullable=False)
    user_email = Column(String, unique=True, index=True, nullable=False)
    user_password = Column(String, nullable=False)

    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    description = Column(String(200), nullable=True)

    registration_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    companies_owned = relationship("Companies", back_populates="owner")
    companies = relationship(
        "Companies",
        secondary="members",
        back_populates="users",
        overlaps="company, members",
        cascade="all, delete"
    )
    notifications = relationship("Notifications", back_populates="user")


class Companies(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    company_name = Column(String, index=True, nullable=False, unique=True)
    is_public = Column(Boolean, default=True)

    description = Column(String(200), nullable=True)

    registration_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("Users", back_populates="companies_owned", cascade='all', single_parent=True)
    users = relationship(
        "Users",
        secondary="members",
        back_populates="companies",
        overlaps="memberships,user",
        cascade="all, delete",
    )
    quizzes = relationship('Quizzes', back_populates='company', cascade='all, delete')


class Quizzes(Base):
    __tablename__ = 'quizzes'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)
    company = relationship('Companies', back_populates='quizzes')

    name = Column(String)
    description = Column(String)
    cooldown_in_days = Column(Integer)
    quiz_questions = relationship('QuizQuestions', back_populates='quizzes', cascade='all, delete')

    @validates('quiz_questions')
    def validate_quiz_questions(self, key, value):
        if len(value) < 2:
            raise ValueError("Quiz must have at least 2 questions")


class QuizQuestions(Base):
    __tablename__ = 'quiz_questions'

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), index=True)
    quizzes = relationship('Quizzes', back_populates='quiz_questions')

    name = Column(String)
    answer_variants = Column(ARRAY(String))
    right_answer = Column(Integer)

    @validates('answer_variants')
    def validate_answer_variants(self, key, value):
        if len(value) < 2:
            raise ValueError("You must have at least 2 variants for answers")


class QuizResults(Base):
    __tablename__ = 'quiz_results'

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), index=True)

    quiz_questions_total = Column(Integer)
    quiz_correct_answers = Column(Integer)
    quiz_correct_answers_percentage = Column(Float)

    summary_questions_total = Column(Integer)
    summary_correct_answers = Column(Integer)
    summary_correct_answers_percentage = Column(Float)

    date_of_quiz = Column(Date, default=date.today, nullable=False)


class Notifications(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)

    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("Users", back_populates="notifications")
