from typing import List

from pydantic import BaseModel

from app.models.models import ActionTypeEnum


class InviteRequest(BaseModel):
    user_id: int
    company_id: int


class CompanyMember(BaseModel):
    user_id: int
    company_id: int
    status: ActionTypeEnum


class CompanyMemberList(BaseModel):
    total: int
    members: List[CompanyMember]


class CompanyMemberStatusChange(BaseModel):
    user_id: int


class CompanyActionRequest(BaseModel):
    user_id: int
    company_id: int
    status: ActionTypeEnum


class CompanyActionResponse(BaseModel):
    id: int
    user_id: int
    company_id: int
    status: ActionTypeEnum


class CompanyActionList(BaseModel):
    total: int
    list: List[CompanyActionResponse]
