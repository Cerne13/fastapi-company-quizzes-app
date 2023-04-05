from databases import Database
from fastapi import APIRouter, Depends

from app.db.connections import get_db
from app.routes.auth import get_current_user
from app.schemas.company_schemas import CompanyListResponse, CompanyResponse, CompanyCreateRequest, CompanyUpdateRequest
from app.schemas.user_schemas import UserResponse
from app.services.auth_service import AuthService
from app.services.companies_service import CompaniesService

router = APIRouter(
    prefix='',
    tags=['companies'],
    responses={
        404: {'description': 'Not found'}
    }
)


@router.get('/companies/', response_model=CompanyListResponse)
async def get_all_companies(
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyListResponse:
    AuthService.check_user_or_403(user=user)

    companies_service = CompaniesService(db=db)
    result = await companies_service.get_all_companies(user=user)
    return result


@router.get('/company/{company_id}/', response_model=CompanyResponse)
async def get_company_by_id(
        company_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyResponse:
    AuthService.check_user_or_403(user=user)

    companies_service = CompaniesService(db=db)
    result = await companies_service.get_company_by_id(user=user, company_id=company_id)
    return result


@router.post('/company/', response_model=CompanyResponse, status_code=201)
async def create_new_company(
        company: CompanyCreateRequest,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyResponse:
    AuthService.check_user_or_403(user=user)

    companies_service = CompaniesService(db=db)
    result = await companies_service.create_new_company(user=user, create_company=company)
    return result


@router.put('/company/{company_id}/', response_model=CompanyResponse)
async def update_company(
        company_id: int,
        update_company: CompanyUpdateRequest,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyResponse:
    AuthService.check_user_or_403(user=user)
    companies_service = CompaniesService(db=db)

    result = await companies_service.update_company(company_id=company_id, update_company=update_company, user=user)
    return result


@router.delete('/company/{company_id}/')
async def delete_company(
        company_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=user)

    companies_service = CompaniesService(db=db)
    await companies_service.delete_company(user=user, company_id=company_id)
