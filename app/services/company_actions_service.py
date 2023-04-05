from asyncpg import UniqueViolationError
from databases import Database
from fastapi import HTTPException
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from app.models.models import Members, ActionTypeEnum, Companies, Users
from app.schemas.company_actions_schemas import CompanyMember, CompanyActionList, CompanyActionRequest, \
    CompanyActionResponse, CompanyMemberList, InviteRequest
from app.schemas.user_schemas import UserResponse


class CompanyActionsService:
    def __init__(self, db: Database):
        self.db = db

    # Helper methods
    async def create_member(self, member_create_request: CompanyMember) -> None:
        create_member_model = Members(
            user_id=member_create_request.user_id,
            company_id=member_create_request.company_id,
            status=member_create_request.status
        )

        query = Members.__table__.insert().values(
            user_id=create_member_model.user_id,
            company_id=create_member_model.company_id,
            status=create_member_model.status
        )
        await self.db.execute(query)

    async def check_company_owned(self, company_id: int, owner_id: int) -> None:
        company_query = select(Companies).where(
            Companies.id == company_id,
            Companies.owner_id == owner_id
        )
        company = await self.db.fetch_one(company_query)

        if not company:
            raise HTTPException(status_code=403, detail="it's not your company")

    async def delete_user(self, company_id: int, user_id: int) -> None:
        user_delete_query = Members.__table__.delete().where(
            Members.user_id == user_id,
            Members.company_id == company_id,
        )
        result = await self.db.execute(user_delete_query)

        if result == 0:
            raise HTTPException(status_code=404, detail='User not found in this company')

    async def check_user_exists(self, user_id: int):
        check_user_query = select(Users).where(Users.id == user_id)
        existing_user = await self.db.fetch_one(check_user_query)
        if not existing_user:
            raise HTTPException(status_code=404, detail='This user not found')

    async def check_company_exists(self, company_id: int):
        check_company_query = select(Companies).where(Companies.id == company_id)
        existing_company = await self.db.fetch_one(check_company_query)
        if not existing_company:
            raise HTTPException(status_code=404, detail='This company not found')

    # Main methods
    async def invite_user(self, payload: InviteRequest, current_user: UserResponse) -> CompanyActionRequest:
        await self.check_user_exists(user_id=payload.user_id)
        await self.check_company_exists(company_id=payload.company_id)
        await self.check_company_owned(company_id=payload.company_id, owner_id=current_user.id)

        if payload.user_id == current_user.id:
            raise HTTPException(status_code=403, detail="You can't invite yourself to your own company.")

        check_query = select(Members).where(
            Members.user_id == payload.user_id,
            Members.company_id == payload.company_id
        )
        check_res = await self.db.fetch_one(check_query)
        if check_res:
            raise HTTPException(status_code=409, detail='User has already been invited to this company')

        request = CompanyActionRequest(
            user_id=payload.user_id,
            company_id=payload.company_id,
            status=ActionTypeEnum.INVITED,
        )
        values = {**request.dict()}
        query = Members.__table__.insert().values(**values)
        await self.db.execute(query=query)

        return request

    async def revoke_invite(self, invite_id: int, current_user: UserResponse) -> None:
        query = select(Members).join(Companies).where(
            Companies.owner_id == current_user.id,
            Members.status == ActionTypeEnum.INVITED,
            Members.id == invite_id
        )
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='Invite not found')

        delete_query = delete(Members).where(Members.id == invite_id)
        await self.db.execute(delete_query)

    async def get_created_invitations(self, current_user: UserResponse) -> CompanyActionList:
        query = select(Members).join(Companies).where(
            Companies.owner_id == current_user.id,
            Members.status == ActionTypeEnum.INVITED
        )
        result = await self.db.fetch_all(query)

        invites = []
        for member in result:
            invites.append(
                CompanyActionResponse(
                    id=member.__getitem__('id'),
                    user_id=member.__getitem__('user_id'),
                    company_id=member.__getitem__('company_id'),
                    status=member.__getitem__('status')
                )
            )
        return CompanyActionList(
            total=len(invites),
            list=invites
        )

    async def get_created_invitations_list_by_company(self, company_id: int, user: UserResponse) -> CompanyActionList:
        await self.check_company_exists(company_id=company_id)
        await self.check_company_owned(company_id=company_id, owner_id=user.id)

        query = select(Members).join(Companies).where(
            Companies.owner_id == user.id,
            Members.company_id == company_id,
            Members.status == ActionTypeEnum.INVITED
        )
        result = await self.db.fetch_all(query)

        invites = []
        for member in result:
            invites.append(
                CompanyActionResponse(
                    id=member.__getitem__('id'),
                    user_id=member.__getitem__('user_id'),
                    company_id=member.__getitem__('company_id'),
                    status=member.__getitem__('status')
                )
            )
        return CompanyActionList(
            total=len(invites),
            list=invites
        )

    async def get_my_invitations_list(self, user: UserResponse) -> CompanyActionList:
        query = Members.__table__.select().options(
            selectinload(Members.company)
        ).where(
            Members.user_id == user.id,
            Members.status == ActionTypeEnum.INVITED
        )
        members = await self.db.fetch_all(query)

        company_invites = []

        for member in members:
            company_invites.append(
                CompanyActionResponse(
                    id=member.__getitem__('id'),
                    user_id=member.__getitem__('user_id'),
                    company_id=member.__getitem__('company_id'),
                    status=member.__getitem__('status')
                )
            )

        return CompanyActionList(
            total=len(company_invites),
            list=company_invites
        )

    async def get_company_members(
            self,
            company_id: int,
            statuses: list[ActionTypeEnum],
            user: UserResponse
    ) -> CompanyMemberList:
        await self.check_company_exists(company_id=company_id)
        await self.check_company_owned(company_id=company_id, owner_id=user.id)

        members_query = select(Members).options(
            selectinload(Members.user)
        ).where(
            Members.company_id == company_id,
            Members.status.in_(statuses)
        )

        members = await self.db.fetch_all(members_query)

        company_members = []
        for member in members:
            company_members.append(
                CompanyMember(
                    user_id=member.__getitem__('user_id'),
                    company_id=member.__getitem__('company_id'),
                    status=member.__getitem__('status')
                )
            )

        return CompanyMemberList(
            total=len(company_members),
            members=company_members
        )

    async def invite_accept(self, invite_id: int, user: UserResponse) -> CompanyMember:
        query = select(Members).where(
            Members.id == invite_id,
            Members.status == ActionTypeEnum.INVITED
        )
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='Invite not found')

        if result.__getitem__('user_id') != user.id:
            raise HTTPException(status_code=400, detail="It is not your invite")

        update_query = update(Members).values(status=ActionTypeEnum.IS_ACTIVE).where(Members.id == invite_id)
        await self.db.execute(update_query)

        updated_query = select(Members).where(Members.id == invite_id)
        updated_result = await self.db.fetch_one(updated_query)

        return CompanyMember(
            user_id=updated_result.__getitem__('user_id'),
            company_id=updated_result.__getitem__('company_id'),
            status=updated_result.__getitem__('status')
        )

    async def invite_decline(self, invite_id: int, user: UserResponse) -> None:
        query = select(Members).where(Members.id == invite_id, Members.status == ActionTypeEnum.INVITED)
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='Invite not found')

        if result.__getitem__('user_id') != user.id:
            raise HTTPException(status_code=400, detail="User does not have an invite to the company")

        query = delete(Members).where(Members.id == invite_id)
        await self.db.execute(query)

    async def get_created_applications(self, user: UserResponse) -> CompanyActionList:
        query = select(Members).where(
            Members.user_id == user.id,
            Members.status == ActionTypeEnum.APPLYING
        )
        result = await self.db.fetch_all(query)

        applies = []
        for member in result:
            applies.append(
                CompanyActionResponse(
                    id=member.__getitem__('id'),
                    user_id=member.__getitem__('user_id'),
                    company_id=member.__getitem__('company_id'),
                    status=member.__getitem__('status')
                )
            )
        return CompanyActionList(
            total=len(applies),
            list=applies
        )

    async def apply_for_company(self, company_id: int, user: UserResponse) -> CompanyActionRequest:
        company_query = select(Companies).where(Companies.id == company_id)
        company = await self.db.fetch_one(company_query)
        if not company:
            raise HTTPException(status_code=404, detail='Company does not exist')

        member_query = select(Members).where(Members.user_id == user.id, Members.company_id == company_id)
        member = await self.db.fetch_one(member_query)

        if member and member.__getitem__('status') == 'applying':
            raise HTTPException(status_code=400, detail='Request already sent')
        elif member:
            raise HTTPException(status_code=400, detail='User is already a member of the company')

        request = CompanyActionRequest(
            user_id=user.id,
            company_id=company_id,
            status=ActionTypeEnum.APPLYING,
        )
        values = {**request.dict()}
        query = Members.__table__.insert().values(**values)

        try:
            await self.db.execute(query=query)
        except UniqueViolationError:
            raise HTTPException(status_code=409, detail='You have already applied to this company')

        return request

    async def revoke_created_apply(self, apply_id: int, user: UserResponse) -> None:
        query = select(Members).where(Members.id == apply_id, Members.status == ActionTypeEnum.APPLYING)
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='Request not found')

        if result.__getitem__('user_id') != user.id:
            raise HTTPException(status_code=403, detail="It's not your request")

        delete_query = delete(Members).where(Members.id == apply_id)
        await self.db.execute(delete_query)

    async def get_applications_for_your_companies(self, user: UserResponse) -> CompanyActionList:
        companies_query = select(Companies.id).where(Companies.owner_id == user.id)
        companies = await self.db.fetch_all(companies_query)

        applications_query = select(Members).where(
            Members.company_id.in_([company['id'] for company in companies]),
            Members.status == ActionTypeEnum.APPLYING
        )
        applications = await self.db.fetch_all(applications_query)
        application_list = [CompanyActionResponse(
            id=row.__getitem__('id'),
            user_id=row.__getitem__('user_id'),
            company_id=row.__getitem__('company_id'),
            status=row.__getitem__('status')
        ) for row in applications]

        return CompanyActionList(
            total=len(application_list),
            list=application_list
        )

    async def get_applies_for_your_company(self, company_id: int, user: UserResponse) -> CompanyActionList:
        await self.check_company_exists(company_id=company_id)
        await self.check_company_owned(company_id=company_id, owner_id=user.id)

        query = select(Members).where(
            Members.company_id == company_id,
            Members.status == ActionTypeEnum.APPLYING
        )
        result = await self.db.fetch_all(query)

        application_list = [CompanyActionResponse(
            id=row.__getitem__('id'),
            user_id=row.__getitem__('user_id'),
            company_id=row.__getitem__('company_id'),
            status=row.__getitem__('status')
        ) for row in result]

        return CompanyActionList(
            total=len(application_list),
            list=application_list
        )

    async def accept_apply(self, apply_id: int, user: UserResponse) -> CompanyActionResponse:

        query = select(Companies).join(Members).where(
            Companies.owner_id == user.id,
            Members.id == apply_id,
            Members.status == ActionTypeEnum.APPLYING
        )
        result = await self.db.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail="Request not found")

        update_query = update(Members).values(status=ActionTypeEnum.IS_ACTIVE).where(Members.id == apply_id)
        await self.db.execute(update_query)

        query = select(Members).where(Members.id == apply_id)
        result = await self.db.fetch_one(query)

        return CompanyActionResponse(
            id=result.__getitem__('id'),
            user_id=result.__getitem__('user_id'),
            company_id=result.__getitem__('company_id'),
            status=result.__getitem__('status')
        )

    async def decline_apply(self, apply_id: int, current_user: UserResponse) -> None:
        query = select(Members).join(Companies).where(
            Companies.owner_id == current_user.id,
            Members.status == ActionTypeEnum.APPLYING,
            Members.id == apply_id
        )
        result = await self.db.fetch_one(query)

        if not result:
            raise HTTPException(status_code=404, detail='Request not found')

        delete_query = Members.__table__.delete().where(Members.id == apply_id)
        await self.db.execute(delete_query)

    async def kick_company_member(self, member_id: int, company_id: int, current_user: UserResponse) -> None:
        await self.check_company_exists(company_id=company_id)
        await self.check_company_owned(company_id=company_id, owner_id=current_user.id)

        query = select(Members).where(
            Members.user_id == member_id,
            Members.status.in_([ActionTypeEnum.IS_ACTIVE, ActionTypeEnum.IS_ADMIN])
        )
        result = await self.db.fetch_one(query)
        if not result:
            raise HTTPException(status_code=404, detail='No such user in the company')

        await self.delete_user(company_id=company_id, user_id=member_id)

    async def leave_company(self, company_id: int, current_user: UserResponse) -> None:
        await self.delete_user(company_id=company_id, user_id=current_user.id)

    async def change_company_member_status(
            self,
            company_id: int,
            member_id: int,
            status: ActionTypeEnum,
            current_user: UserResponse
    ) -> CompanyMember:
        await self.check_company_exists(company_id=company_id)
        await self.check_company_owned(company_id=company_id, owner_id=current_user.id)

        query = select(Members).where(
            Members.user_id == member_id,
            Members.company_id == company_id
        )
        member = await self.db.fetch_one(query)
        if not member:
            raise HTTPException(status_code=404, detail='User not found')

        update_query = update(Members).values(status=status).where(
            Members.user_id == member_id,
            Members.company_id == company_id
        )
        await self.db.execute(update_query)

        updated_member = await self.db.fetch_one(query)

        return CompanyMember(
            user_id=updated_member.__getitem__('user_id'),
            company_id=updated_member.__getitem__('company_id'),
            status=updated_member.__getitem__('status')
        )
