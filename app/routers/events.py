import csv
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlmodel import Session, func, select
from app.core.audit import log_action
from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.age_category import AgeCategory
from app.models.event import Event
from app.models.group import Group
from app.models.participant import Participant
from app.models.user import User, UserRole
from app.schemas.activity import ActivityRead
from app.schemas.age_category import AgeCategoryCreate, AgeCategoryRead
from app.schemas.event import (
    EventDetailRead,
    EventRead,
    GroupDetailRead,
    ImportSummary,
    ParticipantRead,
)
from app.schemas.group import EvaluatorRead

router = APIRouter(prefix="/events", tags=["events"])

REQUIRED_COLUMNS = {"display_name", "group_name"}
KNOWN_COLUMNS = {"display_name", "group_name", "group_identifier", "external_id", "gender", "age"}


@router.get("", response_model=list[EventRead])
def list_events(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    events = session.exec(select(Event)).all()

    group_rows = session.exec(
        select(Group.event_id, func.count(Group.id).label("cnt")).group_by(Group.event_id)
    ).all()
    group_counts = {event_id: cnt for event_id, cnt in group_rows}

    part_rows = session.exec(
        select(Group.event_id, func.count(Participant.id).label("cnt"))
        .join(Participant, Participant.group_id == Group.id)
        .group_by(Group.event_id)
    ).all()
    participant_counts = {event_id: cnt for event_id, cnt in part_rows}

    return [
        EventRead(
            id=event.id,
            name=event.name,
            status=event.status,
            created_by_id=event.created_by_id,
            created_at=event.created_at,
            group_count=group_counts.get(event.id, 0),
            participant_count=participant_counts.get(event.id, 0),
        )
        for event in events
    ]


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

    is_admin = _user.role == UserRole.ADMIN

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
                evaluators=[
                    EvaluatorRead.model_validate(e) for e in group.evaluators
                ],
            )
            for group in event.groups
            if is_admin or any(e.id == _user.id for e in group.evaluators)
        ],
        activities=[
            ActivityRead.model_validate(a) for a in event.activities
        ],
    )


@router.post("/import", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def import_event(
    request: Request,
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
        if len(raw) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file exceeds the 5 MB limit",
            )
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
        gender = row.get("gender") or None
        age_raw = row.get("age", "")
        age = int(age_raw) if age_raw and age_raw.isdigit() else None
        participant = Participant(
            display_name=row["display_name"],
            external_id=row.get("external_id") or None,
            metadata_json=metadata,
            gender=gender,
            age=age,
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
    log_action(
        session, _admin.id, "DELETE_EVENT",
        resource_type="event", resource_id=event_id,
        detail=event.name,
    )
    session.delete(event)
    session.commit()


# ── Age-category endpoints ────────────────────────────────────────────────────

@router.get("/{event_id}/age-categories", response_model=list[AgeCategoryRead])
def list_age_categories(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    cats = session.exec(
        select(AgeCategory).where(AgeCategory.event_id == event_id)
    ).all()
    return [AgeCategoryRead.model_validate(c) for c in cats]


@router.post(
    "/{event_id}/age-categories",
    response_model=AgeCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_age_category(
    event_id: int,
    body: AgeCategoryCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    cat = AgeCategory(event_id=event_id, name=body.name, min_age=body.min_age, max_age=body.max_age)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return AgeCategoryRead.model_validate(cat)


@router.delete(
    "/{event_id}/age-categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_age_category(
    event_id: int,
    category_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    cat = session.get(AgeCategory, category_id)
    if not cat or cat.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Age category not found")
    session.delete(cat)
    session.commit()
