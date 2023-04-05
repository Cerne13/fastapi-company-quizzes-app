from datetime import datetime

from databases import Database
from databases.backends.postgres import Record
from fastapi import HTTPException
from sqlalchemy import select, update, delete

from app.models.models import Companies, ActionTypeEnum
from app.schemas.company_actions_schemas import CompanyMember
from app.schemas.company_schemas import CompanyListResponse, CompanyResponse, CompanyCreateRequest, CompanyUpdateRequest
from app.schemas.user_schemas import UserResponse
from app.services.company_actions_service import CompanyActionsService


class CompaniesService:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def check_404_no_company(company: Record) -> None:
        if not company:
            raise HTTPException(status_code=404, detail='No such company exists')

    @staticmethod
    def check_403_no_rights_or_company_not_public(user: UserResponse, company: CompanyResponse) -> None:
        if user.id != company.owner_id and not company.is_public:
            raise HTTPException(status_code=403, detail='It is not your company and the company is not public.')

    async def get_all_companies(self, user: UserResponse) -> CompanyListResponse:
        query = select(Companies)
        companies = await self.db.fetch_all(query)
        total = len(companies)

        company_list = [CompanyResponse.from_orm(company) for company in companies]

        return CompanyListResponse(
            total=total,
            companies=[
                company for company in company_list
                if user.id == company.owner_id or company.is_public
            ]
        )

    async def get_company_by_id(self, user: UserResponse, company_id: int) -> CompanyResponse:
        query = select(Companies).where(Companies.id == company_id)
        company = await self.db.fetch_one(query)

        self.check_404_no_company(company)

        company_response = CompanyResponse.from_orm(company)

        self.check_403_no_rights_or_company_not_public(user=user, company=company_response)

        return company_response

    async def create_new_company(
            self,
            user: UserResponse,
            create_company: CompanyCreateRequest
    ) -> CompanyResponse:
        if not create_company.company_name:
            raise HTTPException(status_code=422, detail='You must provide a name for the company')

        create_company_model = Companies(
            owner_id=user.id,
            company_name=create_company.company_name,
            is_public=Companies.is_public.default.arg,
            description=create_company.description,

            registration_datetime=datetime.now(),
            update_datetime=datetime.now(),
        )

        query = Companies.__table__.insert().values(
            owner_id=create_company_model.owner_id,
            company_name=create_company_model.company_name,
            is_public=create_company_model.is_public,
            description=create_company_model.description,
            registration_datetime=create_company_model.registration_datetime,
            update_datetime=create_company_model.registration_datetime
        )
        await self.db.execute(query)

        company_query = select(Companies).where(Companies.company_name == create_company.company_name)
        created_company = await self.db.fetch_one(company_query)

        member_create_request = CompanyMember(
            user_id=user.id,
            company_id=created_company.__getitem__('id'),
            status=ActionTypeEnum.IS_ADMIN
        )

        # Create Member table row: user who created the company is the owner
        member_service = CompanyActionsService(db=self.db)
        await member_service.create_member(member_create_request)

        return created_company

    async def update_company(
            self,
            company_id: int,
            update_company: CompanyUpdateRequest,
            user: UserResponse
    ) -> CompanyResponse:
        company = await self.get_company_by_id(user=user, company_id=company_id)

        if user.id != company.owner_id:
            raise HTTPException(status_code=403, detail="You can't edit another users' companies")

        update_data = update_company.dict(exclude_unset=True)
        update_data['update_datetime'] = datetime.now()

        update_query = update(Companies).where(Companies.id == company_id).values(**update_data)
        await self.db.execute(update_query)

        company_query = select(Companies).where(Companies.id == company_id)
        updated_company = await self.db.fetch_one(company_query)
        return updated_company

    async def delete_company(self, user: UserResponse, company_id: int) -> None:
        query = select(Companies).where(Companies.id == company_id)
        company = await self.db.fetch_one(query)

        self.check_404_no_company(company)

        company_response = CompanyResponse.from_orm(company)

        if user.id != company_response.owner_id:
            raise HTTPException(status_code=403, detail="You can't delete other users companies")

        delete_query = delete(Companies).where(Companies.id == company_id)
        await self.db.execute(delete_query)
