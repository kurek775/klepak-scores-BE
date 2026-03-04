"""Unified authorization helpers for evaluator visibility restrictions."""

from sqlmodel import Session, select

from app.core.exceptions import ForbiddenException
from app.models.event_evaluator import EventEvaluator
from app.models.group import Group
from app.models.group_evaluator import GroupEvaluator
from app.models.user import User, UserRole


def is_admin(user: User) -> bool:
    return user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)


def require_event_access(session: Session, user: User, event_id: int) -> None:
    """Raise ForbiddenException if evaluator is not in the event pool."""
    if is_admin(user):
        return
    pool = session.get(EventEvaluator, (event_id, user.id))
    if not pool:
        raise ForbiddenException("You do not have access to this event")


def get_visible_group_ids(session: Session, user: User, event_id: int) -> list[int] | None:
    """Return group IDs visible to the user, or None if admin (all visible)."""
    if is_admin(user):
        return None  # all groups visible
    group_ids = session.exec(
        select(GroupEvaluator.group_id)
        .join(Group, GroupEvaluator.group_id == Group.id)
        .where(GroupEvaluator.user_id == user.id, Group.event_id == event_id)
    ).all()
    return list(group_ids)
