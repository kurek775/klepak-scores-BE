from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.dependencies import get_current_admin
from app.database import get_session
from app.models.user import User
from app.schemas.participant import ParticipantCreate, ParticipantMoveRequest, ParticipantRead, ParticipantUpdate
from app.services import participant_service

router = APIRouter(tags=["participants"])


@router.post("/groups/{group_id}/participants", response_model=ParticipantRead, status_code=status.HTTP_201_CREATED)
def add_participant(
    group_id: int,
    body: ParticipantCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return participant_service.add_participant(session, group_id, body)


@router.patch("/participants/{participant_id}", response_model=ParticipantRead)
def update_participant(
    participant_id: int,
    body: ParticipantUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return participant_service.update_participant(session, participant_id, body)


@router.delete("/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    participant_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    participant_service.delete_participant(session, participant_id)


@router.post("/participants/{participant_id}/move", response_model=ParticipantRead)
def move_participant(
    participant_id: int,
    body: ParticipantMoveRequest,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return participant_service.move_participant(session, participant_id, body)
