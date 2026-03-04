"""Event domain service — business logic extracted from routers/events.py."""

import csv
import io
import json as json_module

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.audit import log_action
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.activity import Activity
from app.models.age_category import AgeCategory
from app.models.diploma_template import DiplomaOrientation, DiplomaTemplate
from app.models.event import Event
from app.models.event_evaluator import EventEvaluator
from app.models.group import Group
from app.models.group_evaluator import GroupEvaluator
from app.models.participant import Participant
from app.models.user import User, UserRole
from app.schemas.activity import ActivityRead
from app.schemas.age_category import AgeCategoryCreate, AgeCategoryRead
from app.schemas.event import (
    CsvPreviewResponse,
    EventDetailRead,
    EventRead,
    EventUpdate,
    ImportSummary,
    ManualEventCreate,
)
from app.schemas.group import EvaluatorRead, GroupCreate, GroupDetailRead
from app.schemas.participant import ParticipantRead
from app.services.common import get_or_404

REQUIRED_COLUMNS = {"display_name", "group_name"}
KNOWN_COLUMNS = {"display_name", "group_name", "group_identifier", "external_id", "gender", "age"}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_default_diploma(session: Session, event_id: int) -> None:
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


def _read_csv_content(file) -> str:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationException("File must be a .csv file")
    try:
        raw = file.file.read()
        if len(raw) > 5 * 1024 * 1024:
            raise ValidationException("CSV file exceeds the 5 MB limit")
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValidationException("File must be UTF-8 encoded")


# ── Event CRUD ───────────────────────────────────────────────────────────────


def list_events(session: Session, user: User) -> list[EventRead]:
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
    stmt = select(Event, group_count_sq, part_count_sq)
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        # Evaluators: only events where they're in the pool
        pool_event_ids = select(EventEvaluator.event_id).where(EventEvaluator.user_id == user.id)
        stmt = stmt.where(Event.id.in_(pool_event_ids))
    rows = session.exec(stmt).all()
    return [
        EventRead(
            id=event.id, name=event.name, status=event.status,
            created_by_id=event.created_by_id, created_at=event.created_at,
            group_count=group_count, participant_count=participant_count,
        )
        for event, group_count, participant_count in rows
    ]


def create_event_manual(session: Session, body: ManualEventCreate, admin: User) -> ImportSummary:
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
                display_name=p.display_name, external_id=p.external_id,
                gender=p.gender, age=p.age, group_id=group.id,
            )
            session.add(participant)
            participant_count += 1

    _create_default_diploma(session, event.id)
    log_action(
        session, admin.id, "CREATE_EVENT_MANUAL",
        resource_type="event", resource_id=event.id,
        detail=f"{body.name}: {len(body.groups)} groups, {participant_count} participants",
    )
    session.commit()

    return ImportSummary(
        event_id=event.id, event_name=event.name,
        groups_created=len(body.groups), participants_created=participant_count,
    )


def get_event_detail(session: Session, event_id: int, user: User) -> EventDetailRead:
    event = session.exec(
        select(Event).where(Event.id == event_id).options(
            selectinload(Event.groups).selectinload(Group.evaluators),
            selectinload(Event.groups).selectinload(Group.participants),
            selectinload(Event.activities),
            selectinload(Event.event_evaluators),
        )
    ).first()
    if not event:
        raise NotFoundException("Event", event_id)

    is_admin = user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    pool_user_ids = [ee.user_id for ee in event.event_evaluators]
    pool_users = []
    if pool_user_ids:
        pool_users = session.exec(select(User).where(User.id.in_(pool_user_ids))).all()

    return EventDetailRead(
        id=event.id, name=event.name, status=event.status,
        created_by_id=event.created_by_id, created_at=event.created_at,
        groups=[
            GroupDetailRead(
                id=group.id, name=group.name, identifier=group.identifier,
                participants=[ParticipantRead.model_validate(p) for p in group.participants],
                evaluators=[EvaluatorRead.model_validate(e) for e in group.evaluators],
            )
            for group in event.groups
            if is_admin or any(e.id == user.id for e in group.evaluators)
        ],
        activities=[ActivityRead.model_validate(a) for a in event.activities],
        event_evaluators=[EvaluatorRead.model_validate(u) for u in pool_users],
    )


def update_event(session: Session, event_id: int, body: EventUpdate, admin: User) -> EventRead:
    event = get_or_404(session, Event, event_id, "Event")

    if body.name is not None:
        event.name = body.name
    if body.status is not None:
        event.status = body.status

    session.add(event)
    log_action(
        session, admin.id, "UPDATE_EVENT",
        resource_type="event", resource_id=event_id,
        detail=f"name={event.name}, status={event.status.value}",
    )
    session.commit()
    session.refresh(event)

    group_count = session.exec(select(func.count(Group.id)).where(Group.event_id == event_id)).one()
    part_count = session.exec(
        select(func.count(Participant.id)).join(Group, Group.id == Participant.group_id).where(Group.event_id == event_id)
    ).one()
    return EventRead(
        id=event.id, name=event.name, status=event.status,
        created_by_id=event.created_by_id, created_at=event.created_at,
        group_count=group_count, participant_count=part_count,
    )


def create_group(session: Session, event_id: int, body: GroupCreate) -> GroupDetailRead:
    get_or_404(session, Event, event_id, "Event")
    group = Group(name=body.name, identifier=body.identifier, event_id=event_id)
    session.add(group)
    session.commit()
    session.refresh(group)
    return GroupDetailRead(id=group.id, name=group.name, identifier=group.identifier, participants=[], evaluators=[])


def delete_event(session: Session, event_id: int, admin: User) -> None:
    event = get_or_404(session, Event, event_id, "Event")
    log_action(
        session, admin.id, "DELETE_EVENT",
        resource_type="event", resource_id=event_id, detail=event.name,
    )
    session.delete(event)
    session.commit()


# ── CSV Preview / Import ─────────────────────────────────────────────────────


def preview_csv(file) -> CsvPreviewResponse:
    content = _read_csv_content(file)
    reader = csv.reader(io.StringIO(content))
    all_rows = list(reader)
    if not all_rows:
        raise ValidationException("CSV file is empty or has no headers")
    headers = [h.strip() for h in all_rows[0]]
    data_rows = all_rows[1:]
    return CsvPreviewResponse(headers=headers, sample_rows=data_rows[:5], total_rows=len(data_rows))


def import_event(session: Session, event_name: str, file, column_mapping: str | None, admin: User) -> ImportSummary:
    event_name = event_name.strip()
    if not event_name or len(event_name) > 255:
        raise ValidationException("Event name must be between 1 and 255 characters")

    content = _read_csv_content(file)
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise ValidationException("CSV file is empty or has no headers")

    rows = _parse_csv_rows(reader, column_mapping)

    if not rows:
        raise ValidationException("CSV file contains no data rows")
    if len(rows) > 10_000:
        raise ValidationException(f"CSV file contains {len(rows)} rows — maximum is 10,000")

    event = Event(name=event_name, created_by_id=admin.id)
    session.add(event)
    session.flush()

    group_map: dict[str, Group] = {}
    for row, _extra in rows:
        group_name = row["group_name"]
        if group_name not in group_map:
            identifier = row.get("group_identifier", "")
            group = Group(name=group_name, identifier=identifier, event_id=event.id)
            session.add(group)
            session.flush()
            group_map[group_name] = group

    participant_count = 0
    for row, extra in rows:
        group = group_map[row["group_name"]]
        gender = row.get("gender") or None
        age_raw = row.get("age", "")
        age = int(age_raw) if age_raw and age_raw.isdigit() else None
        participant = Participant(
            display_name=row["display_name"], external_id=row.get("external_id") or None,
            metadata_json=extra if extra else None, gender=gender, age=age, group_id=group.id,
        )
        session.add(participant)
        participant_count += 1

    _create_default_diploma(session, event.id)
    session.commit()

    return ImportSummary(
        event_id=event.id, event_name=event.name,
        groups_created=len(group_map), participants_created=participant_count,
    )


def _parse_csv_rows(reader: csv.DictReader, column_mapping: str | None) -> list[tuple[dict, dict | None]]:
    """Parse CSV rows, applying column mapping if provided."""
    if column_mapping:
        try:
            mapping = json_module.loads(column_mapping)
        except (json_module.JSONDecodeError, TypeError):
            raise ValidationException("column_mapping must be valid JSON")

        invalid_fields = set(mapping.values()) - KNOWN_COLUMNS
        if invalid_fields:
            raise ValidationException(f"Unknown system fields in mapping: {', '.join(sorted(invalid_fields))}")
        mapped_system_fields = set(mapping.values())
        missing = REQUIRED_COLUMNS - mapped_system_fields
        if missing:
            raise ValidationException(f"Mapping must include required fields: {', '.join(sorted(missing))}")

        rows: list[tuple[dict, dict | None]] = []
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
                raise ValidationException(f"Row {i}: display_name is required")
            if not row.get("group_name"):
                raise ValidationException(f"Row {i}: group_name is required")
            rows.append((row, extra if extra else None))
        return rows
    else:
        headers = [h.strip().lower() for h in reader.fieldnames]
        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise ValidationException(f"Missing required columns: {', '.join(sorted(missing))}")
        extra_columns = [h for h in headers if h not in KNOWN_COLUMNS]

        rows = []
        for i, raw_row in enumerate(reader, start=2):
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}
            if not row.get("display_name"):
                raise ValidationException(f"Row {i}: display_name is required")
            if not row.get("group_name"):
                raise ValidationException(f"Row {i}: group_name is required")
            extra = {col: row.get(col, "") for col in extra_columns} if extra_columns else None
            rows.append((row, extra))
        return rows


# ── Event Evaluator Pool ─────────────────────────────────────────────────────


def list_event_evaluators(session: Session, event_id: int) -> list[EvaluatorRead]:
    get_or_404(session, Event, event_id, "Event")
    ee_rows = session.exec(select(EventEvaluator).where(EventEvaluator.event_id == event_id)).all()
    user_ids = [ee.user_id for ee in ee_rows]
    if not user_ids:
        return []
    users = session.exec(select(User).where(User.id.in_(user_ids))).all()
    return [EvaluatorRead.model_validate(u) for u in users]


def add_event_evaluator(session: Session, event_id: int, user_id: int) -> None:
    get_or_404(session, Event, event_id, "Event")
    user = get_or_404(session, User, user_id, "User")
    if not user.is_active:
        raise ValidationException("User is not active")
    if user.role != UserRole.EVALUATOR:
        raise ValidationException("User is not an evaluator")

    existing = session.get(EventEvaluator, (event_id, user_id))
    if existing:
        raise ConflictException("Evaluator already assigned to this event")

    link = EventEvaluator(event_id=event_id, user_id=user_id)
    session.add(link)
    session.commit()


def remove_event_evaluator(session: Session, event_id: int, user_id: int, admin: User) -> None:
    link = session.get(EventEvaluator, (event_id, user_id))
    if not link:
        raise NotFoundException("Assignment")

    group_ids = session.exec(select(Group.id).where(Group.event_id == event_id)).all()
    if group_ids:
        group_links = session.exec(
            select(GroupEvaluator).where(GroupEvaluator.user_id == user_id, GroupEvaluator.group_id.in_(group_ids))
        ).all()
        for gl in group_links:
            session.delete(gl)

    log_action(
        session, admin.id, "DELETE_EVENT_EVALUATOR",
        resource_type="event", resource_id=event_id, detail=f"user_id={user_id}",
    )
    session.delete(link)
    session.commit()


# ── Age Categories ───────────────────────────────────────────────────────────


def list_age_categories(session: Session, event_id: int) -> list[AgeCategoryRead]:
    get_or_404(session, Event, event_id, "Event")
    cats = session.exec(select(AgeCategory).where(AgeCategory.event_id == event_id)).all()
    return [AgeCategoryRead.model_validate(c) for c in cats]


def create_age_category(session: Session, event_id: int, body: AgeCategoryCreate) -> AgeCategoryRead:
    get_or_404(session, Event, event_id, "Event")
    cat = AgeCategory(event_id=event_id, name=body.name, min_age=body.min_age, max_age=body.max_age)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return AgeCategoryRead.model_validate(cat)


def delete_age_category(session: Session, event_id: int, category_id: int) -> None:
    cat = session.get(AgeCategory, category_id)
    if not cat or cat.event_id != event_id:
        raise NotFoundException("Age category", category_id)
    session.delete(cat)
    session.commit()
