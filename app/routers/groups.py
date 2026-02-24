from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.core.audit import log_action
from app.core.dependencies import get_current_active_user, get_current_admin
from app.database import get_session
from app.models.event_evaluator import EventEvaluator
from app.models.group import Group
from app.models.group_evaluator import GroupEvaluator
from app.models.user import User
from app.schemas.group import AssignEvaluatorRequest, EvaluatorRead, MyGroupRead

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/my-groups", response_model=list[MyGroupRead])
def my_groups(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    stmt = (
        select(GroupEvaluator.group_id)
        .where(GroupEvaluator.user_id == user.id)
    )
    group_ids = session.exec(stmt).all()

    if not group_ids:
        return []

    groups = session.exec(
        select(Group).where(Group.id.in_(group_ids)).options(
            selectinload(Group.event),
            selectinload(Group.participants),
        )
    ).all()
    return [
        MyGroupRead(
            id=g.id,
            name=g.name,
            identifier=g.identifier,
            event_id=g.event_id,
            event_name=g.event.name,
            participant_count=len(g.participants),
        )
        for g in groups
    ]


@router.post("/{group_id}/evaluators", status_code=status.HTTP_201_CREATED)
def assign_evaluator(
    group_id: int,
    body: AssignEvaluatorRequest,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    user = session.get(User, body.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check evaluator is in the event pool first
    event_id = group.event_id
    event_link = session.get(EventEvaluator, (event_id, body.user_id))
    if not event_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evaluator must be assigned to the event first",
        )

    existing = session.get(GroupEvaluator, (group_id, body.user_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evaluator already assigned to this group",
        )

    # Check if evaluator is already assigned to another group in the same event
    # Use FOR UPDATE to prevent race conditions on concurrent assignments
    conflict = session.exec(
        select(GroupEvaluator)
        .join(Group, GroupEvaluator.group_id == Group.id)
        .where(GroupEvaluator.user_id == body.user_id, Group.event_id == event_id)
        .with_for_update()
    ).first()
    if conflict:
        conflict_group = session.get(Group, conflict.group_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Evaluator is already assigned to group '{conflict_group.name}' in this event",
        )

    link = GroupEvaluator(group_id=group_id, user_id=body.user_id)
    session.add(link)
    session.commit()
    return {"detail": "Evaluator assigned"}


@router.delete(
    "/{group_id}/evaluators/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_evaluator(
    group_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    link = session.get(GroupEvaluator, (group_id, user_id))
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    log_action(
        session, _admin.id, "DELETE_GROUP_EVALUATOR",
        resource_type="group", resource_id=group_id,
        detail=f"user_id={user_id}",
    )
    session.delete(link)
    session.commit()


@router.get("/{group_id}/evaluators", response_model=list[EvaluatorRead])
def list_group_evaluators(
    group_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    return [EvaluatorRead.model_validate(e) for e in group.evaluators]
