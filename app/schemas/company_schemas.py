from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CompanyCreateRequest(BaseModel):
    company_name: str
    description: Optional[str]


class CompanyResponse(BaseModel):
    id: int
    owner_id: int
    company_name: str
    is_public: bool
    description: Optional[str]

    registration_datetime: datetime
    update_datetime: datetime

    class Config:
        orm_mode = True


class CompanyListResponse(BaseModel):
    total: int
    companies: List[CompanyResponse]


class CompanyUpdateRequest(BaseModel):
    company_name: Optional[str]
    description: Optional[str]
    is_public: Optional[bool]
