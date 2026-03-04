from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.authorization import require_event_access
from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.user import User
from app.schemas.leaderboard import LeaderboardResponse
from app.services import leaderboard_service

router = APIRouter(tags=["analytics"])


@router.get("/events/{event_id}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    event_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    require_event_access(session, user, event_id)
    return leaderboard_service.get_leaderboard(session, event_id)


@router.get("/events/{event_id}/export-csv")
@limiter.limit("10/minute")
def export_csv(
    request: Request,
    event_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    csv_content = leaderboard_service.export_csv(session, event_id)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_results.csv"},
    )
