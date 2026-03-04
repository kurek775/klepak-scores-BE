from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.services import activity_service

router = APIRouter(tags=["activities"])


@router.post("/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_activity(
    request: Request,
    body: ActivityCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return activity_service.create_activity(session, body)


@router.get("/events/{event_id}/activities", response_model=list[ActivityRead])
def list_event_activities(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    return activity_service.list_event_activities(session, event_id)


@router.patch("/activities/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: int,
    body: ActivityUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return activity_service.update_activity(session, activity_id, body)


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def delete_activity(
    request: Request,
    activity_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    activity_service.delete_activity(session, activity_id)
