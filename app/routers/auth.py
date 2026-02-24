import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.config import settings
from app.core.audit import log_action
from app.core.dependencies import get_current_user
from app.core.email import send_password_reset_email
from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_session
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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.ADMIN,
        is_active=False,
    )
    session.add(user)
    session.flush()
    log_action(session, user.id, "REGISTER", resource_type="user", resource_id=user.id)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.password_hash):
        log_action(session, None, "LOGIN_FAILED", detail=body.email)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not yet approved",
        )
    log_action(session, user.id, "LOGIN", resource_type="user", resource_id=user.id)
    session.commit()
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/validate-invitation")
@limiter.limit("3/minute")
def validate_invitation(
    request: Request,
    token: str,
    session: Session = Depends(get_session),
):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    inv = session.exec(
        select(InvitationToken).where(InvitationToken.token_hash == token_hash)
    ).first()

    if not inv or inv.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used invitation token",
        )

    if inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation token has expired",
        )

    return {"email": inv.email, "role": inv.role}


@router.post("/accept-invitation", response_model=TokenResponse)
@limiter.limit("5/minute")
def accept_invitation(
    request: Request,
    body: AcceptInvitationRequest,
    session: Session = Depends(get_session),
):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    inv = session.exec(
        select(InvitationToken).where(InvitationToken.token_hash == token_hash).with_for_update()
    ).first()

    if not inv or inv.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used invitation token",
        )

    if inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation token has expired",
        )

    # Check if user already exists
    existing = session.exec(select(User).where(User.email == inv.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=inv.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole(inv.role),
        is_active=True,
    )
    session.add(user)
    session.flush()

    inv.used = True
    session.add(inv)

    log_action(session, user.id, "ACCEPT_INVITATION", resource_type="user", resource_id=user.id)
    session.commit()

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    # Always return 200 to prevent email enumeration
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user:
        log_action(session, None, "FORGOT_PASSWORD_UNKNOWN", detail=body.email)
        session.commit()
        return {"detail": "If that email exists, a reset link has been sent."}

    # Invalidate any previous unused tokens for this user
    old_tokens = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,  # noqa: E712
        )
    ).all()
    for t in old_tokens:
        t.used = True
        session.add(t)

    # Generate a new token
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
    )
    session.add(reset_token)
    log_action(session, user.id, "FORGOT_PASSWORD", resource_type="user", resource_id=user.id)
    session.commit()

    # Send email (or print to console in dev mode)
    send_password_reset_email(user.email, user.full_name, raw_token)

    return {"detail": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()

    reset_token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash).with_for_update()
    ).first()

    if not reset_token or reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token",
        )

    if reset_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    user = session.get(User, reset_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    user.password_hash = hash_password(body.new_password)
    reset_token.used = True

    session.add(user)
    session.add(reset_token)
    log_action(session, user.id, "RESET_PASSWORD", resource_type="user", resource_id=user.id)
    session.commit()

    return {"detail": "Password has been reset successfully."}
