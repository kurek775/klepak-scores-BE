"""Activity domain service — business logic extracted from routers/activities.py."""

from sqlmodel import Session, func, select

from app.core.exceptions import ValidationException
from app.models.activity import Activity
from app.models.event import Event
from app.models.record import Record
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.services.common import get_or_404, invalidate_leaderboard_cache


def _record_count(session: Session, activity_id: int) -> int:
    return session.exec(select(func.count(Record.id)).where(Record.activity_id == activity_id)).one()


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
    if body.evaluation_type is not None and body.evaluation_type != activity.evaluation_type:
        # Changing the scoring type would reinterpret existing scores (e.g. a
        # numeric value read as a time), so lock it once results exist.
        if _record_count(session, activity_id) > 0:
            raise ValidationException(
                "Cannot change the scoring type — this activity already has recorded scores"
            )
        activity.evaluation_type = body.evaluation_type
    session.add(activity)
    session.commit()
    session.refresh(activity)
    invalidate_leaderboard_cache(activity.event_id)
    return ActivityRead.model_validate(activity)


def delete_activity(session: Session, activity_id: int) -> None:
    activity = get_or_404(session, Activity, activity_id, "Activity")
    event_id = activity.event_id
    session.delete(activity)
    session.commit()
    invalidate_leaderboard_cache(event_id)
