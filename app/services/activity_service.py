"""Activity domain service — business logic extracted from routers/activities.py."""

from sqlmodel import Session, select

from app.models.activity import Activity
from app.models.event import Event
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.services.common import get_or_404


def create_activity(session: Session, body: ActivityCreate) -> ActivityRead:
    get_or_404(session, Event, body.event_id, "Event")
    activity = Activity(
        name=body.name, description=body.description,
        evaluation_type=body.evaluation_type, event_id=body.event_id,
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return ActivityRead.model_validate(activity)


def list_event_activities(session: Session, event_id: int) -> list[ActivityRead]:
    get_or_404(session, Event, event_id, "Event")
    activities = session.exec(select(Activity).where(Activity.event_id == event_id)).all()
    return [ActivityRead.model_validate(a) for a in activities]


def update_activity(session: Session, activity_id: int, body: ActivityUpdate) -> ActivityRead:
    activity = get_or_404(session, Activity, activity_id, "Activity")
    if body.name is not None:
        activity.name = body.name
    if body.description is not None:
        activity.description = body.description
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return ActivityRead.model_validate(activity)


def delete_activity(session: Session, activity_id: int) -> None:
    activity = get_or_404(session, Activity, activity_id, "Activity")
    session.delete(activity)
    session.commit()
