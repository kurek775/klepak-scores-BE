from fastapi import HTTPException, status

from app.models.user import User, UserRole


def require_admin(user: User) -> None:
    """Raise 403 if the user is not ADMIN or SUPER_ADMIN."""
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
