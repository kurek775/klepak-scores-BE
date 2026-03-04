"""Group domain service — business logic extracted from routers/groups.py."""

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.audit import log_action
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.models.event_evaluator import EventEvaluator
from app.models.group import Group
from app.models.group_evaluator import GroupEvaluator
from app.models.participant import Participant
from app.models.user import User, UserRole
from app.schemas.group import AssignEvaluatorRequest, EvaluatorRead, GroupUpdate, MyGroupRead
from app.services.common import get_or_404


def my_groups(session: Session, user: User) -> list[MyGroupRead]:
    stmt = select(GroupEvaluator.group_id).where(GroupEvaluator.user_id == user.id)
    group_ids = session.exec(stmt).all()
    if not group_ids:
        return []

    groups = session.exec(
        select(Group).where(Group.id.in_(group_ids)).options(
            selectinload(Group.event), selectinload(Group.participants),
        )
    ).all()
    return [
        MyGroupRead(
            id=g.id, name=g.name, identifier=g.identifier,
            event_id=g.event_id, event_name=g.event.name,
            participant_count=len(g.participants),
        )
        for g in groups
    ]


def update_group(session: Session, group_id: int, body: GroupUpdate) -> MyGroupRead:
    group = session.exec(
        select(Group).where(Group.id == group_id).options(
            selectinload(Group.event), selectinload(Group.participants),
        )
    ).first()
    if not group:
        raise NotFoundException("Group", group_id)

    if body.name is not None:
        group.name = body.name
    if body.identifier is not None:
        group.identifier = body.identifier
    session.add(group)
    session.commit()
    session.refresh(group)
    return MyGroupRead(
        id=group.id, name=group.name, identifier=group.identifier,
        event_id=group.event_id, event_name=group.event.name,
        participant_count=len(group.participants),
    )


def delete_group(session: Session, group_id: int) -> None:
    group = get_or_404(session, Group, group_id, "Group")
    participant_count = session.exec(
        select(func.count(Participant.id)).where(Participant.group_id == group_id)
    ).one()
    if participant_count > 0:
        raise ValidationException(
            f"Cannot delete group — it still has {participant_count} participant(s). Remove or move them first."
        )
    session.delete(group)
    session.commit()


def assign_evaluator(session: Session, group_id: int, body: AssignEvaluatorRequest) -> None:
    group = get_or_404(session, Group, group_id, "Group")
    user = get_or_404(session, User, body.user_id, "User")

    if not user.is_active:
        raise ValidationException("User is not active")

    event_id = group.event_id

    pool_check = session.get(EventEvaluator, (event_id, body.user_id))
    if not pool_check:
        raise ValidationException("Evaluator must be assigned to this event first")

    existing = session.get(GroupEvaluator, (group_id, body.user_id))
    if existing:
        raise ConflictException("Evaluator already assigned to this group")

    conflict = session.exec(
        select(GroupEvaluator)
        .join(Group, GroupEvaluator.group_id == Group.id)
        .where(GroupEvaluator.user_id == body.user_id, Group.event_id == event_id)
        .with_for_update()
    ).first()
    if conflict:
        conflict_group = session.get(Group, conflict.group_id)
        raise ConflictException(f"Evaluator is already assigned to group '{conflict_group.name}' in this event")

    link = GroupEvaluator(group_id=group_id, user_id=body.user_id)
    session.add(link)
    session.commit()


def remove_evaluator(session: Session, group_id: int, user_id: int, admin: User) -> None:
    link = session.get(GroupEvaluator, (group_id, user_id))
    if not link:
        raise NotFoundException("Assignment")
    log_action(
        session, admin.id, "DELETE_GROUP_EVALUATOR",
        resource_type="group", resource_id=group_id, detail=f"user_id={user_id}",
    )
    session.delete(link)
    session.commit()


def list_group_evaluators(session: Session, group_id: int, user: User) -> list[EvaluatorRead]:
    group = get_or_404(session, Group, group_id, "Group")
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        own_link = session.get(GroupEvaluator, (group_id, user.id))
        if not own_link:
            raise ForbiddenException("You are not assigned to this group")
    return [EvaluatorRead.model_validate(e) for e in group.evaluators]
