"""Admin domain service — business logic extracted from routers/admin.py."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.config import settings
from app.core.audit import log_action
from app.core.email import send_invitation_email
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.models.invitation_token import InvitationToken
from app.models.user import User, UserRole
from app.schemas.auth import CreateInvitationRequest, InvitationRead, UserRead, UserUpdate
from app.services.common import get_or_404

logger = logging.getLogger(__name__)


def list_users(session: Session, skip: int, limit: int) -> list[UserRead]:
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return [UserRead.model_validate(u) for u in users]


def update_user(session: Session, user_id: int, body: UserUpdate, admin: User) -> UserRead:
    user = get_or_404(session, User, user_id, "User")

    if user.role == UserRole.SUPER_ADMIN:
        raise ForbiddenException("Cannot modify super admin accounts")

    if body.role is not None:
        if body.role == UserRole.SUPER_ADMIN:
            raise ForbiddenException("Cannot assign super admin role")
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
    return UserRead.model_validate(user)


def create_invitation(session: Session, body: CreateInvitationRequest, admin: User) -> InvitationRead:
    existing_user = session.exec(select(User).where(User.email == body.email)).first()
    if existing_user:
        raise ConflictException("Email already registered")

    if body.role == UserRole.SUPER_ADMIN:
        raise ForbiddenException("Cannot invite super admins")
    if body.role == UserRole.ADMIN and admin.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Only super admins can invite admins")

    existing_inv = session.exec(
        select(InvitationToken).where(
            InvitationToken.email == body.email,
            InvitationToken.used == False,  # noqa: E712
            InvitationToken.expires_at > datetime.now(timezone.utc),
        )
    ).first()
    if existing_inv:
        raise ConflictException("A pending invitation already exists for this email")

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    inv = InvitationToken(
        email=body.email, role=body.role,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.INVITATION_EXPIRE_DAYS),
        invited_by=admin.id,
    )
    session.add(inv)
    session.flush()

    log_action(
        session, admin.id, "INVITE_EVALUATOR",
        resource_type="invitation", resource_id=inv.id, detail=body.email,
    )
    session.commit()
    session.refresh(inv)

    try:
        send_invitation_email(body.email, body.role.value, raw_token)
    except Exception:
        logger.exception("Failed to send invitation email to %s", body.email)

    return InvitationRead.model_validate(inv)


def list_invitations(session: Session) -> list[InvitationRead]:
    invitations = session.exec(
        select(InvitationToken).where(
            InvitationToken.expires_at > datetime.now(timezone.utc),
        ).order_by(InvitationToken.created_at.desc())
    ).all()
    return [InvitationRead.model_validate(i) for i in invitations]


def resend_invitation(session: Session, invitation_id: int, admin: User) -> InvitationRead:
    inv = get_or_404(session, InvitationToken, invitation_id, "Invitation")
    if inv.used:
        raise ValidationException("Invitation already used")

    raw_token = secrets.token_urlsafe(48)
    inv.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    inv.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.INVITATION_EXPIRE_DAYS)
    session.add(inv)
    log_action(
        session, admin.id, "RESEND_INVITATION",
        resource_type="invitation", resource_id=inv.id, detail=inv.email,
    )
    session.commit()
    session.refresh(inv)

    try:
        send_invitation_email(inv.email, inv.role, raw_token)
    except Exception:
        logger.exception("Failed to send invitation email to %s", inv.email)

    return InvitationRead.model_validate(inv)


def revoke_invitation(session: Session, invitation_id: int, admin: User) -> None:
    inv = get_or_404(session, InvitationToken, invitation_id, "Invitation")
    if inv.used:
        raise ValidationException("Invitation already used")

    inv.used = True
    session.add(inv)
    log_action(
        session, admin.id, "REVOKE_INVITATION",
        resource_type="invitation", resource_id=inv.id, detail=inv.email,
    )
    session.commit()
