from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.database import get_session
from app.models.user import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, session: Session = Depends(get_session)):
    return auth_service.register(session, body)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, session: Session = Depends(get_session)):
    return auth_service.login(session, body)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/validate-invitation")
@limiter.limit("3/minute")
def validate_invitation(request: Request, token: str, session: Session = Depends(get_session)):
    return auth_service.validate_invitation(session, token)


@router.post("/accept-invitation", response_model=TokenResponse)
@limiter.limit("5/minute")
def accept_invitation(request: Request, body: AcceptInvitationRequest, session: Session = Depends(get_session)):
    return auth_service.accept_invitation(session, body)


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, body: ForgotPasswordRequest, session: Session = Depends(get_session)):
    return auth_service.forgot_password(session, body)


@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, body: ResetPasswordRequest, session: Session = Depends(get_session)):
    return auth_service.reset_password(session, body)
