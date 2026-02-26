import csv
import io
import json as json_module

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select
from app.core.audit import log_action
from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.activity import Activity
from app.models.age_category import AgeCategory
from app.models.event import Event
from app.models.event_evaluator import EventEvaluator
from app.models.group import Group
from app.models.group_evaluator import GroupEvaluator
from app.models.participant import Participant
from app.models.user import User, UserRole
from app.schemas.activity import ActivityRead
from app.schemas.age_category import AgeCategoryCreate, AgeCategoryRead
from app.models.diploma_template import DiplomaTemplate, DiplomaOrientation
from app.schemas.event import (
    CsvPreviewResponse,
    EventDetailRead,
    EventRead,
    EventUpdate,
    GroupCreate,
    GroupDetailRead,
    ImportSummary,
    ManualEventCreate,
    ParticipantRead,
)
from app.schemas.group import EvaluatorRead

router = APIRouter(prefix="/events", tags=["events"])

REQUIRED_COLUMNS = {"display_name", "group_name"}
KNOWN_COLUMNS = {"display_name", "group_name", "group_identifier", "external_id", "gender", "age"}


def _create_default_diploma(session: Session, event_id: int) -> None:
    """Create a default diploma template for a newly created event."""
    default_tpl = DiplomaTemplate(
        event_id=event_id,
        name="Default",
        orientation=DiplomaOrientation.LANDSCAPE,
        items=[
            {"type": "DYNAMIC", "key": "participant_name", "x": 50, "y": 38, "fontSize": 42, "fontWeight": "bold",   "color": "#1a1a1a", "centerH": True, "centerV": False},
            {"type": "DYNAMIC", "key": "place",            "x": 50, "y": 56, "fontSize": 30, "fontWeight": "normal", "color": "#444444", "centerH": True, "centerV": False},
            {"type": "DYNAMIC", "key": "activity",         "x": 50, "y": 68, "fontSize": 20, "fontWeight": "normal", "color": "#666666", "centerH": True, "centerV": False},
        ],
        fonts=[],
        default_font=None,
    )
    session.add(default_tpl)


@router.get("", response_model=list[EventRead])
def list_events(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    group_count_sq = (
        select(func.count(Group.id))
        .where(Group.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
        .label("group_count")
    )
    part_count_sq = (
        select(func.count(Participant.id))
        .join(Group, Group.id == Participant.group_id)
        .where(Group.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
        .label("participant_count")
    )

    rows = session.exec(select(Event, group_count_sq, part_count_sq)).all()

    return [
        EventRead(
            id=event.id,
            name=event.name,
            status=event.status,
            created_by_id=event.created_by_id,
            created_at=event.created_at,
            group_count=group_count,
            participant_count=participant_count,
        )
        for event, group_count, participant_count in rows
    ]


@router.post("/manual", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_event_manual(
    request: Request,
    body: ManualEventCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    event = Event(name=body.name, created_by_id=admin.id)
    session.add(event)
    session.flush()

    participant_count = 0
    for g in body.groups:
        group = Group(name=g.name, identifier=g.identifier, event_id=event.id)
        session.add(group)
        session.flush()
        for p in g.participants:
            participant = Participant(
                display_name=p.display_name,
                external_id=p.external_id,
                gender=p.gender,
                age=p.age,
                group_id=group.id,
            )
            session.add(participant)
            participant_count += 1

    session.commit()

    _create_default_diploma(session, event.id)
    session.commit()

    log_action(
        session, admin.id, "CREATE_EVENT_MANUAL",
        resource_type="event", resource_id=event.id,
        detail=f"{body.name}: {len(body.groups)} groups, {participant_count} participants",
    )
    session.commit()

    return ImportSummary(
        event_id=event.id,
        event_name=event.name,
        groups_created=len(body.groups),
        participants_created=participant_count,
    )


@router.get("/{event_id}", response_model=EventDetailRead)
def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    event = session.exec(
        select(Event).where(Event.id == event_id).options(
            selectinload(Event.groups).selectinload(Group.evaluators),
            selectinload(Event.groups).selectinload(Group.participants),
            selectinload(Event.activities),
            selectinload(Event.event_evaluators),
        )
    ).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    is_admin = _user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    # Resolve event evaluator user info
    pool_user_ids = [ee.user_id for ee in event.event_evaluators]
    pool_users = []
    if pool_user_ids:
        pool_users = session.exec(select(User).where(User.id.in_(pool_user_ids))).all()

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
        event_evaluators=[
            EvaluatorRead.model_validate(u) for u in pool_users
        ],
    )


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    body: EventUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if body.name is not None:
        event.name = body.name
    if body.status is not None:
        event.status = body.status

    session.add(event)
    log_action(
        session, _admin.id, "UPDATE_EVENT",
        resource_type="event", resource_id=event_id,
        detail=f"name={event.name}, status={event.status.value}",
    )
    session.commit()
    session.refresh(event)

    group_count = session.exec(
        select(func.count(Group.id)).where(Group.event_id == event_id)
    ).one()
    part_count = session.exec(
        select(func.count(Participant.id))
        .join(Group, Group.id == Participant.group_id)
        .where(Group.event_id == event_id)
    ).one()

    return EventRead(
        id=event.id,
        name=event.name,
        status=event.status,
        created_by_id=event.created_by_id,
        created_at=event.created_at,
        group_count=group_count,
        participant_count=part_count,
    )


@router.post("/{event_id}/groups", response_model=GroupDetailRead, status_code=status.HTTP_201_CREATED)
def create_group(
    event_id: int,
    body: GroupCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    group = Group(name=body.name, identifier=body.identifier, event_id=event_id)
    session.add(group)
    session.commit()
    session.refresh(group)
    return GroupDetailRead(
        id=group.id,
        name=group.name,
        identifier=group.identifier,
        participants=[],
        evaluators=[],
    )


def _read_csv_content(file: UploadFile) -> str:
    """Read and validate a CSV upload, returning decoded content."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv file",
        )
    try:
        raw = file.file.read()
        if len(raw) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file exceeds the 5 MB limit",
            )
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )


@router.post("/preview-csv", response_model=CsvPreviewResponse)
@limiter.limit("10/minute")
def preview_csv(
    request: Request,
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
):
    content = _read_csv_content(file)
    reader = csv.reader(io.StringIO(content))
    all_rows = list(reader)
    if not all_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or has no headers",
        )

    headers = [h.strip() for h in all_rows[0]]
    data_rows = all_rows[1:]
    sample = data_rows[:5]

    return CsvPreviewResponse(
        headers=headers,
        sample_rows=sample,
        total_rows=len(data_rows),
    )


@router.post("/import", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def import_event(
    request: Request,
    event_name: str = Form(...),
    file: UploadFile = File(...),
    column_mapping: str | None = Form(default=None),
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    event_name = event_name.strip()
    if not event_name or len(event_name) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event name must be between 1 and 255 characters",
        )

    content = _read_csv_content(file)

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or has no headers",
        )

    # If column_mapping provided, remap CSV headers to system field names
    if column_mapping:
        try:
            mapping = json_module.loads(column_mapping)
        except (json_module.JSONDecodeError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="column_mapping must be valid JSON",
            )

        # mapping: {"CSV Header": "system_field", ...}
        invalid_fields = set(mapping.values()) - KNOWN_COLUMNS
        if invalid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown system fields in mapping: {', '.join(sorted(invalid_fields))}",
            )
        mapped_system_fields = set(mapping.values())
        missing = REQUIRED_COLUMNS - mapped_system_fields
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mapping must include required fields: {', '.join(sorted(missing))}",
            )

        # Build reverse lookup: original_csv_header -> system_field
        # Extra CSV columns (not in mapping) go to metadata_json
        rows = []
        for i, raw_row in enumerate(reader, start=2):
            row: dict[str, str] = {}
            extra: dict[str, str] = {}
            for csv_col, value in raw_row.items():
                csv_col_stripped = csv_col.strip()
                val = value.strip() if value else ""
                system_field = mapping.get(csv_col_stripped)
                if system_field:
                    row[system_field] = val
                else:
                    extra[csv_col_stripped] = val
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
            if extra:
                row["_extra"] = ""  # marker
                row["_extra_data"] = ""
            rows.append((row, extra if extra else None))
    else:
        # Original behavior: normalize headers to lowercase
        headers = [h.strip().lower() for h in reader.fieldnames]
        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(sorted(missing))}",
            )

        extra_columns = [h for h in headers if h not in KNOWN_COLUMNS]

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
            extra = {col: row.get(col, "") for col in extra_columns} if extra_columns else None
            rows.append((row, extra))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file contains no data rows",
        )

    if len(rows) > 10_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV file contains {len(rows)} rows — maximum is 10,000",
        )

    # Create Event
    event = Event(name=event_name, created_by_id=admin.id)
    session.add(event)
    session.flush()

    # Deduplicate and create groups
    group_map: dict[str, Group] = {}
    for row, _extra in rows:
        group_name = row["group_name"]
        if group_name not in group_map:
            identifier = row.get("group_identifier", "")
            group = Group(name=group_name, identifier=identifier, event_id=event.id)
            session.add(group)
            session.flush()
            group_map[group_name] = group

    # Create participants
    participant_count = 0
    for row, extra in rows:
        group = group_map[row["group_name"]]
        gender = row.get("gender") or None
        age_raw = row.get("age", "")
        age = int(age_raw) if age_raw and age_raw.isdigit() else None
        participant = Participant(
            display_name=row["display_name"],
            external_id=row.get("external_id") or None,
            metadata_json=extra if extra else None,
            gender=gender,
            age=age,
            group_id=group.id,
        )
        session.add(participant)
        participant_count += 1

    session.commit()

    _create_default_diploma(session, event.id)
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

    # DB-level ON DELETE CASCADE handles all child rows automatically
    session.delete(event)
    session.commit()


# ── Event evaluator pool endpoints ─────────────────────────────────────────────

@router.get("/{event_id}/evaluators", response_model=list[EvaluatorRead])
def list_event_evaluators(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    ee_rows = session.exec(
        select(EventEvaluator).where(EventEvaluator.event_id == event_id)
    ).all()
    user_ids = [ee.user_id for ee in ee_rows]
    if not user_ids:
        return []
    users = session.exec(select(User).where(User.id.in_(user_ids))).all()
    return [EvaluatorRead.model_validate(u) for u in users]


@router.post("/{event_id}/evaluators", status_code=status.HTTP_201_CREATED)
def add_event_evaluator(
    event_id: int,
    body: dict,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not active")
    if user.role != UserRole.EVALUATOR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an evaluator")

    existing = session.get(EventEvaluator, (event_id, user_id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evaluator already assigned to this event")

    link = EventEvaluator(event_id=event_id, user_id=user_id)
    session.add(link)
    session.commit()
    return {"detail": "Evaluator added to event"}


@router.delete(
    "/{event_id}/evaluators/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_event_evaluator(
    event_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    link = session.get(EventEvaluator, (event_id, user_id))
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Cascade: also remove group assignments for this user in this event
    group_ids = session.exec(
        select(Group.id).where(Group.event_id == event_id)
    ).all()
    if group_ids:
        group_links = session.exec(
            select(GroupEvaluator).where(
                GroupEvaluator.user_id == user_id,
                GroupEvaluator.group_id.in_(group_ids),
            )
        ).all()
        for gl in group_links:
            session.delete(gl)

    log_action(
        session, _admin.id, "DELETE_EVENT_EVALUATOR",
        resource_type="event", resource_id=event_id,
        detail=f"user_id={user_id}",
    )
    session.delete(link)
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
