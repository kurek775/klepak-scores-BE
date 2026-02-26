from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.core.dependencies import get_current_active_user
from app.core.permissions import require_admin
from app.database import get_session
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead, PaginatedAuditLogs

router = APIRouter(tags=["audit"])


@router.get("/admin/audit-logs", response_model=PaginatedAuditLogs)
def get_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    require_admin(current_user)

    total = session.exec(select(func.count(AuditLog.id))).one()
    logs = session.exec(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    ).all()

    return PaginatedAuditLogs(
        total=total,
        skip=skip,
        limit=limit,
        items=[AuditLogRead.model_validate(log) for log in logs],
    )
