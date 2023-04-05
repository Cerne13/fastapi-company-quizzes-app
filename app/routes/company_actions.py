from databases import Database
from fastapi import APIRouter, Depends, HTTPException

from app.db.connections import get_db
from app.models.models import ActionTypeEnum
from app.routes.auth import get_current_user
from app.schemas.company_actions_schemas import CompanyActionList, CompanyActionResponse, CompanyMemberList, \
    CompanyMember, CompanyActionRequest, InviteRequest, CompanyMemberStatusChange
from app.schemas.user_schemas import UserResponse
from app.services.auth_service import AuthService
from app.services.company_actions_service import CompanyActionsService

router = APIRouter(
    prefix='',
    tags=['company actions'],
    responses={
        404: {'description': 'Not found'}
    }
)


@router.get('/created_invitations', response_model=CompanyActionList)
async def get_created_invitations(
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db),
) -> CompanyActionList:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.get_created_invitations(current_user=user)
    return result


@router.get('/invite/my', response_model=CompanyActionList)
async def get_my_invitations_list(
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db),

) -> CompanyActionList:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.get_my_invitations_list(user=user)
    return result


@router.get('/invite/company/{company_id}/', response_model=CompanyActionList)
async def get_my_invitations_by_company(
        company_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db),
) -> CompanyActionList:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.get_created_invitations_list_by_company(company_id=company_id, user=user)
    return result


@router.post('/invite/', response_model=CompanyActionRequest, status_code=201)
async def create_invite(
        payload: InviteRequest,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyActionRequest:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.invite_user(payload=payload, current_user=current_user)
    return result


@router.delete('/invite/{invite_id}/', status_code=200)
async def revoke_invite(
        invite_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.revoke_invite(invite_id=invite_id, current_user=current_user)


@router.get('/invite/{invite_id}/accept/', response_model=CompanyMember)
async def accept_invite(
        invite_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyMember:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.invite_accept(invite_id=invite_id, user=user)
    return result


@router.get('/invite/{invite_id}/decline/', status_code=200)
async def decline_invite(
        invite_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.invite_decline(invite_id=invite_id, user=user)


@router.get('/request/my', response_model=CompanyActionList)
async def get_my_applications(
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyActionList:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.get_created_applications(user=user)
    return result


@router.post('/request/{company_id}', response_model=CompanyActionRequest, status_code=200)
async def apply_for_company(
        company_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyActionRequest:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.apply_for_company(company_id=company_id, user=user)
    return result


@router.get('/request/company/{company_id}/', response_model=CompanyActionList, status_code=200)
async def get_applies_for_company(
        company_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyActionList:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.get_applies_for_your_company(company_id=company_id, user=user)
    return result


@router.delete('/request/{apply_id}/', status_code=200)
async def revoke_created_apply(
        apply_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.revoke_created_apply(apply_id=apply_id, user=user)


@router.get('/applications/my_companies', response_model=CompanyActionList)
async def get_applications_for_my_companies(
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyActionList:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.get_applications_for_your_companies(user=user)
    return result


@router.get('/request/{apply_id}/accept/', response_model=CompanyActionResponse)
async def accept_apply(
        apply_id: int,
        user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyActionResponse:
    AuthService.check_user_or_403(user=user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.accept_apply(apply_id=apply_id, user=user)
    return result


@router.get('/request/{apply_id}/decline', status_code=200)
async def decline_apply(
        apply_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.decline_apply(apply_id=apply_id, current_user=current_user)


@router.get('/company/{company_id}/members', response_model=CompanyMemberList)
async def get_all_company_members(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyMemberList:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    statuses = [ActionTypeEnum.IS_ACTIVE, ActionTypeEnum.IS_ADMIN]

    result = await actions_service.get_company_members(
        company_id=company_id,
        statuses=statuses,
        user=current_user
    )
    return result


@router.delete('/company/{company_id}/member/{member_id}/', status_code=200)
async def kick_company_member(
        member_id: int,
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.kick_company_member(
        member_id=member_id,
        company_id=company_id,
        current_user=current_user
    )


@router.delete('/company/{company_id}/leave', status_code=200)
async def leave_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.leave_company(company_id=company_id, current_user=current_user)


@router.get('/company/{company_id}/admins', response_model=CompanyMemberList)
async def get_company_admins(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyMemberList:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    statuses = [ActionTypeEnum.IS_ADMIN]

    result = await actions_service.get_company_members(
        company_id=company_id,
        statuses=statuses,
        user=current_user
    )
    return result


@router.post('/company/{company_id}/admin/', status_code=200, response_model=CompanyMember)
async def promote_member_to_admin(
        company_id: int,
        user_id: CompanyMemberStatusChange,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyMember:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.change_company_member_status(
        company_id=company_id,
        member_id=user_id.user_id,
        current_user=current_user,
        status=ActionTypeEnum.IS_ADMIN
    )

    return result


@router.post('/company/{company_id}/admin_demote/', status_code=200, response_model=CompanyMember)
async def demote_admin_to_member(
        company_id: int,
        user_id: CompanyMemberStatusChange,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> CompanyMember:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    result = await actions_service.change_company_member_status(
        company_id=company_id,
        member_id=user_id.user_id,
        current_user=current_user,
        status=ActionTypeEnum.IS_ACTIVE
    )

    return result


@router.delete('/company/{company_id}/admin/{member_id}', status_code=200)
async def kick_admin(
        member_id: int,
        company_id: int,
        current_user: UserResponse = Depends(get_current_user),
        db: Database = Depends(get_db)
) -> None:
    AuthService.check_user_or_403(user=current_user)
    actions_service = CompanyActionsService(db=db)

    await actions_service.kick_company_member(
        member_id=member_id,
        company_id=company_id,
        current_user=current_user
    )
