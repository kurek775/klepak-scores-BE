import csv
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user, get_current_admin
from app.database import get_session
from app.models.event import Event
from app.models.group import Group
from app.models.participant import Participant
from app.models.user import User
from app.schemas.event import (
    EventDetailRead,
    EventRead,
    GroupDetailRead,
    ImportSummary,
    ParticipantRead,
)

router = APIRouter(prefix="/events", tags=["events"])

REQUIRED_COLUMNS = {"display_name", "group_name"}
KNOWN_COLUMNS = {"display_name", "group_name", "group_identifier", "external_id"}


@router.get("", response_model=list[EventRead])
def list_events(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    events = session.exec(select(Event)).all()
    result = []
    for event in events:
        group_count = len(event.groups)
        participant_count = sum(len(g.participants) for g in event.groups)
        result.append(
            EventRead(
                id=event.id,
                name=event.name,
                status=event.status,
                created_by_id=event.created_by_id,
                created_at=event.created_at,
                group_count=group_count,
                participant_count=participant_count,
            )
        )
    return result


@router.get("/{event_id}", response_model=EventDetailRead)
def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return EventDetailRead(
        id=event.id,
        name=event.name,
        status=event.status,
        created_by_id=event.created_by_id,
        created_at=event.created_at,
        groups=[
            GroupDetailRead(
                id=group.id,
                name=group.name,
                identifier=group.identifier,
                participants=[
                    ParticipantRead.model_validate(p) for p in group.participants
                ],
            )
            for group in event.groups
        ],
    )


@router.post("/import", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
def import_event(
    event_name: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv file",
        )

    # Read and decode file content (utf-8-sig handles Excel BOM)
    try:
        raw = file.file.read()
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or has no headers",
        )

    # Normalize headers to lowercase
    headers = [h.strip().lower() for h in reader.fieldnames]
    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    # Identify extra columns for metadata
    extra_columns = [h for h in headers if h not in KNOWN_COLUMNS]

    # Parse rows
    rows = []
    for i, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}
        if not row.get("display_name"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row {i}: display_name is required",
            )
        if not row.get("group_name"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row {i}: group_name is required",
            )
        rows.append(row)

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file contains no data rows",
        )

    # Create Event
    event = Event(name=event_name, created_by_id=admin.id)
    session.add(event)
    session.flush()

    # Deduplicate and create groups
    group_map: dict[str, Group] = {}
    for row in rows:
        group_name = row["group_name"]
        if group_name not in group_map:
            identifier = row.get("group_identifier", "")
            group = Group(name=group_name, identifier=identifier, event_id=event.id)
            session.add(group)
            session.flush()
            group_map[group_name] = group

    # Create participants
    participant_count = 0
    for row in rows:
        group = group_map[row["group_name"]]
        metadata = {col: row.get(col, "") for col in extra_columns} if extra_columns else None
        participant = Participant(
            display_name=row["display_name"],
            external_id=row.get("external_id") or None,
            metadata_json=metadata,
            group_id=group.id,
        )
        session.add(participant)
        participant_count += 1

    session.commit()

    return ImportSummary(
        event_id=event.id,
        event_name=event.name,
        groups_created=len(group_map),
        participants_created=participant_count,
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    session.delete(event)
    session.commit()
