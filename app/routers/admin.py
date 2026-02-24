import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.config import settings
from app.core.audit import log_action
from app.core.dependencies import get_current_admin, get_current_super_admin
from app.core.email import send_invitation_email
from app.core.limiter import limiter
from app.database import get_session
from app.models.invitation_token import InvitationToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    CreateInvitationRequest,
    InvitationRead,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── User management (super admin only) ──────────────────────────────

@router.get("/users", response_model=list[UserRead])
def list_users(
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin),
):
    users = session.exec(select(User)).all()
    return users


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    body: UserUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify super admin accounts",
        )

    if body.role is not None:
        if body.role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign super admin role",
            )
        log_action(
            session, admin.id, "CHANGE_ROLE",
            resource_type="user", resource_id=user.id,
            detail=f"{user.role} -> {body.role}",
        )
        user.role = body.role

    if body.is_active is not None:
        log_action(
            session, admin.id, "CHANGE_STATUS",
            resource_type="user", resource_id=user.id,
            detail=f"is_active={body.is_active}",
        )
        user.is_active = body.is_active

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ── Invitation management (any admin) ───────────────────────────────

@router.post("/invitations", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_invitation(
    request: Request,
    body: CreateInvitationRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.email == body.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check for existing unused invitation
    existing_inv = session.exec(
        select(InvitationToken).where(
            InvitationToken.email == body.email,
            InvitationToken.used == False,  # noqa: E712
            InvitationToken.expires_at > datetime.now(timezone.utc),
        )
    ).first()
    if existing_inv:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation already exists for this email",
        )

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    inv = InvitationToken(
        email=body.email,
        role="EVALUATOR",
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.INVITATION_EXPIRE_DAYS),
        invited_by=admin.id,
    )
    session.add(inv)
    session.flush()

    log_action(
        session, admin.id, "INVITE_EVALUATOR",
        resource_type="invitation", resource_id=inv.id,
        detail=body.email,
    )
    session.commit()
    session.refresh(inv)

    send_invitation_email(body.email, "EVALUATOR", raw_token)

    return inv


@router.get("/invitations", response_model=list[InvitationRead])
def list_invitations(
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    invitations = session.exec(
        select(InvitationToken).where(
            InvitationToken.expires_at > datetime.now(timezone.utc),
        ).order_by(InvitationToken.created_at.desc())  # type: ignore[union-attr]
    ).all()
    return invitations


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin),
):
    inv = session.get(InvitationToken, invitation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if inv.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already used",
        )

    inv.used = True
    session.add(inv)
    log_action(
        session, admin.id, "REVOKE_INVITATION",
        resource_type="invitation", resource_id=inv.id,
        detail=inv.email,
    )
    session.commit()
