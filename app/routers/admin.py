from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.core.dependencies import get_current_admin, get_current_super_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.user import User
from app.schemas.auth import CreateInvitationRequest, InvitationRead, UserRead, UserUpdate
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return admin_service.list_users(session, skip, limit)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    body: UserUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin),
):
    return admin_service.update_user(session, user_id, body, admin)


@router.post("/invitations", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_invitation(
    request: Request,
    body: CreateInvitationRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    return admin_service.create_invitation(session, body, admin)


@router.get("/invitations", response_model=list[InvitationRead])
def list_invitations(
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return admin_service.list_invitations(session)


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationRead)
@limiter.limit("10/minute")
def resend_invitation(
    request: Request,
    invitation_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    return admin_service.resend_invitation(session, invitation_id, admin)


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    admin_service.revoke_invitation(session, invitation_id, admin)
