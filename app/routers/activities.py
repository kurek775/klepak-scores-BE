from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.activity import Activity
from app.models.event import Event
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityRead

router = APIRouter(tags=["activities"])


@router.post("/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_activity(
    request: Request,
    body: ActivityCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event = session.get(Event, body.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    activity = Activity(
        name=body.name,
        description=body.description,
        evaluation_type=body.evaluation_type,
        event_id=body.event_id,
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return ActivityRead.model_validate(activity)


@router.get("/events/{event_id}/activities", response_model=list[ActivityRead])
def list_event_activities(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    activities = session.exec(
        select(Activity).where(Activity.event_id == event_id)
    ).all()
    return [ActivityRead.model_validate(a) for a in activities]


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def delete_activity(
    request: Request,
    activity_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    session.delete(activity)
    session.commit()
