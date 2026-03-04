"""Participant domain service — business logic extracted from routers/participants.py."""

from sqlmodel import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.models.group import Group
from app.models.participant import Participant
from app.schemas.participant import ParticipantCreate, ParticipantMoveRequest, ParticipantRead, ParticipantUpdate
from app.services.common import get_or_404


def add_participant(session: Session, group_id: int, body: ParticipantCreate) -> ParticipantRead:
    get_or_404(session, Group, group_id, "Group")
    participant = Participant(
        display_name=body.display_name, external_id=body.external_id,
        gender=body.gender, age=body.age, group_id=group_id,
    )
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return ParticipantRead.model_validate(participant)


def update_participant(session: Session, participant_id: int, body: ParticipantUpdate) -> ParticipantRead:
    participant = get_or_404(session, Participant, participant_id, "Participant")
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


def delete_participant(session: Session, participant_id: int) -> None:
    participant = get_or_404(session, Participant, participant_id, "Participant")
    session.delete(participant)
    session.commit()


def move_participant(session: Session, participant_id: int, body: ParticipantMoveRequest) -> ParticipantRead:
    participant = get_or_404(session, Participant, participant_id, "Participant")
    target_group = get_or_404(session, Group, body.group_id, "Target group")

    source_group = session.get(Group, participant.group_id)
    if source_group.event_id != target_group.event_id:
        raise ValidationException("Cannot move participant to a group in a different event")

    participant.group_id = body.group_id
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return ParticipantRead.model_validate(participant)
