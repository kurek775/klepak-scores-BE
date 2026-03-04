"""Auth domain service — business logic extracted from routers/auth.py."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.config import settings
from app.core.audit import log_action
from app.core.email import send_password_reset_email
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, UnauthorizedException, ValidationException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.invitation_token import InvitationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    AcceptInvitationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
)


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC). SQLite returns naive datetimes."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _validate_token(session: Session, token_str: str, model_class):
    """Hash token, look up, check used/expired. Returns the DB row."""
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    row = session.exec(
        select(model_class).where(model_class.token_hash == token_hash).with_for_update()
    ).first()
    if not row or row.used:
        raise ValidationException(f"Invalid or already used {'reset' if model_class is PasswordResetToken else 'invitation'} token")
    if _ensure_aware(row.expires_at) < datetime.now(timezone.utc):
        raise ValidationException(f"{'Reset' if model_class is PasswordResetToken else 'Invitation'} token has expired")
    return row


def register(session: Session, body: RegisterRequest) -> UserRead:
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise ConflictException("Email already registered")

    user = User(
        email=body.email, password_hash=hash_password(body.password),
        full_name=body.full_name, role=UserRole.ADMIN, is_active=False,
    )
    session.add(user)
    session.flush()
    log_action(session, user.id, "REGISTER", resource_type="user", resource_id=user.id)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user)


def login(session: Session, body: LoginRequest) -> TokenResponse:
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.password_hash):
        log_action(session, None, "LOGIN_FAILED", detail=body.email)
        session.commit()
        raise UnauthorizedException("Invalid email or password")
    if not user.is_active:
        raise ForbiddenException("Account not yet approved")
    log_action(session, user.id, "LOGIN", resource_type="user", resource_id=user.id)
    session.commit()
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


def validate_invitation(session: Session, token: str) -> dict:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    inv = session.exec(select(InvitationToken).where(InvitationToken.token_hash == token_hash)).first()
    if not inv or inv.used:
        raise ValidationException("Invalid or already used invitation token")
    if _ensure_aware(inv.expires_at) < datetime.now(timezone.utc):
        raise ValidationException("Invitation token has expired")
    return {"email": inv.email, "role": inv.role}


def accept_invitation(session: Session, body: AcceptInvitationRequest) -> TokenResponse:
    inv = _validate_token(session, body.token, InvitationToken)

    existing = session.exec(select(User).where(User.email == inv.email)).first()
    if existing:
        raise ConflictException("Email already registered")

    user = User(
        email=inv.email, password_hash=hash_password(body.password),
        full_name=body.full_name, role=UserRole(inv.role), is_active=True,
    )
    session.add(user)
    session.flush()

    inv.used = True
    session.add(inv)
    log_action(session, user.id, "ACCEPT_INVITATION", resource_type="user", resource_id=user.id)
    session.commit()

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


def forgot_password(session: Session, body: ForgotPasswordRequest) -> dict:
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user:
        log_action(session, None, "FORGOT_PASSWORD_UNKNOWN", detail=body.email)
        session.commit()
        return {"detail": "If that email exists, a reset link has been sent."}

    old_tokens = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,  # noqa: E712
        )
    ).all()
    for t in old_tokens:
        t.used = True
        session.add(t)

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset_token = PasswordResetToken(
        user_id=user.id, token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
    )
    session.add(reset_token)
    log_action(session, user.id, "FORGOT_PASSWORD", resource_type="user", resource_id=user.id)
    session.commit()

    send_password_reset_email(user.email, user.full_name, raw_token)
    return {"detail": "If that email exists, a reset link has been sent."}


def reset_password(session: Session, body: ResetPasswordRequest) -> dict:
    reset_token = _validate_token(session, body.token, PasswordResetToken)

    user = session.get(User, reset_token.user_id)
    if not user:
        raise ValidationException("User not found")

    user.password_hash = hash_password(body.new_password)
    reset_token.used = True
    session.add(user)
    session.add(reset_token)
    log_action(session, user.id, "RESET_PASSWORD", resource_type="user", resource_id=user.id)
    session.commit()

    return {"detail": "Password has been reset successfully."}
