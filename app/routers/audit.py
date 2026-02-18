from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user
from app.database import get_session
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogRead

router = APIRouter(tags=["audit"])


@router.get("/admin/audit-logs", response_model=list[AuditLogRead])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    logs = session.exec(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    ).all()
    return logs
