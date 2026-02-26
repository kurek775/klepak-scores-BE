from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_admin
from app.database import get_session
from app.models.group import Group
from app.models.participant import Participant
from app.models.user import User
from app.schemas.event import ParticipantCreate, ParticipantMoveRequest, ParticipantRead, ParticipantUpdate

router = APIRouter(tags=["participants"])


@router.post(
    "/groups/{group_id}/participants",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
def add_participant(
    group_id: int,
    body: ParticipantCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    participant = Participant(
        display_name=body.display_name,
        external_id=body.external_id,
        gender=body.gender,
        age=body.age,
        group_id=group_id,
    )
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return ParticipantRead.model_validate(participant)


@router.patch("/participants/{participant_id}", response_model=ParticipantRead)
def update_participant(
    participant_id: int,
    body: ParticipantUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    if body.display_name is not None:
        participant.display_name = body.display_name
    if body.external_id is not None:
        participant.external_id = body.external_id
    if body.gender is not None:
        participant.gender = body.gender
    if body.age is not None:
        participant.age = body.age

    session.add(participant)
    session.commit()
    session.refresh(participant)
    return ParticipantRead.model_validate(participant)


@router.delete("/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    participant_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    session.delete(participant)
    session.commit()


@router.post("/participants/{participant_id}/move", response_model=ParticipantRead)
def move_participant(
    participant_id: int,
    body: ParticipantMoveRequest,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    target_group = session.get(Group, body.group_id)
    if not target_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target group not found")

    # Ensure same event
    source_group = session.get(Group, participant.group_id)
    if source_group.event_id != target_group.event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot move participant to a group in a different event",
        )

    participant.group_id = body.group_id
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return ParticipantRead.model_validate(participant)
