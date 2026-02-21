from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, or_, select

from app.core.audit import log_action
from app.core.dependencies import get_current_admin
from app.database import get_session
from app.models.user import User, UserRole
from app.schemas.auth import UserRead, UserUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    users = session.exec(
        select(User).where(
            or_(User.role != UserRole.ADMIN, User.id == admin.id)
        )
    ).all()
    return users


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    body: UserUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify admin accounts",
        )

    if body.role is not None:
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
