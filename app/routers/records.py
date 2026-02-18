from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user
from app.database import get_session
from app.models.activity import Activity
from app.models.group import Group
from app.models.group_evaluator import GroupEvaluator
from app.models.participant import Participant
from app.models.record import Record
from app.models.user import User
from app.schemas.activity import BulkRecordCreate, RecordCreate, RecordRead

router = APIRouter(tags=["records"])


def _check_evaluator_access(session: Session, user: User, participant_id: int) -> None:
    """Verify that the user is assigned as evaluator to the participant's group."""
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participant {participant_id} not found",
        )
    link = session.exec(
        select(GroupEvaluator).where(
            GroupEvaluator.group_id == participant.group_id,
            GroupEvaluator.user_id == user.id,
        )
    ).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this participant's group",
        )


def _upsert_record(
    session: Session, user: User, activity_id: int, participant_id: int, value_raw: str | int
) -> Record:
    """Insert or update a record for a participant/activity pair."""
    existing = session.exec(
        select(Record).where(
            Record.participant_id == participant_id,
            Record.activity_id == activity_id,
        )
    ).first()
    value_str = str(value_raw)
    if existing:
        existing.value_raw = value_str
        existing.evaluator_id = user.id
        session.add(existing)
        return existing
    record = Record(
        value_raw=value_str,
        participant_id=participant_id,
        activity_id=activity_id,
        evaluator_id=user.id,
    )
    session.add(record)
    return record


@router.post("/records", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def submit_record(
    body: RecordCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    activity = session.get(Activity, body.activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    _check_evaluator_access(session, user, body.participant_id)
    record = _upsert_record(session, user, body.activity_id, body.participant_id, body.value_raw)
    session.commit()
    session.refresh(record)
    return RecordRead.model_validate(record)


@router.post("/records/bulk", response_model=list[RecordRead], status_code=status.HTTP_201_CREATED)
def submit_bulk_records(
    body: BulkRecordCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    activity = session.get(Activity, body.activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    results: list[Record] = []
    for entry in body.records:
        _check_evaluator_access(session, user, entry.participant_id)
        record = _upsert_record(session, user, body.activity_id, entry.participant_id, entry.value_raw)
        results.append(record)
    session.commit()
    for r in results:
        session.refresh(r)
    return [RecordRead.model_validate(r) for r in results]


@router.get(
    "/activities/{activity_id}/records",
    response_model=list[RecordRead],
)
def get_activity_records(
    activity_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    records = session.exec(
        select(Record).where(Record.activity_id == activity_id)
    ).all()
    return [RecordRead.model_validate(r) for r in records]
