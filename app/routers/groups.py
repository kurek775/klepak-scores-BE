from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.dependencies import get_current_active_user, get_current_admin
from app.database import get_session
from app.models.user import User
from app.schemas.group import AssignEvaluatorRequest, EvaluatorRead, GroupUpdate, MyGroupRead
from app.services import group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/my-groups", response_model=list[MyGroupRead])
def my_groups(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return group_service.my_groups(session, user)


@router.patch("/{group_id}", response_model=MyGroupRead)
def update_group(
    group_id: int,
    body: GroupUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return group_service.update_group(session, group_id, body)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    group_service.delete_group(session, group_id)


@router.post("/{group_id}/evaluators", status_code=status.HTTP_201_CREATED)
def assign_evaluator(
    group_id: int,
    body: AssignEvaluatorRequest,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    group_service.assign_evaluator(session, group_id, body)
    return {"detail": "Evaluator assigned"}


@router.delete("/{group_id}/evaluators/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_evaluator(
    group_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    group_service.remove_evaluator(session, group_id, user_id, admin)


@router.get("/{group_id}/evaluators", response_model=list[EvaluatorRead])
def list_group_evaluators(
    group_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return group_service.list_group_evaluators(session, group_id, user)
