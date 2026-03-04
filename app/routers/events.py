from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlmodel import Session

from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.limiter import limiter
from app.database import get_session
from app.models.user import User
from app.schemas.age_category import AgeCategoryCreate, AgeCategoryRead
from app.schemas.event import (
    CsvPreviewResponse,
    EventDetailRead,
    EventEvaluatorAdd,
    EventRead,
    EventUpdate,
    ImportSummary,
    ManualEventCreate,
)
from app.schemas.group import EvaluatorRead, GroupCreate, GroupDetailRead
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
def list_events(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return event_service.list_events(session, user)


@router.post("/manual", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_event_manual(
    request: Request,
    body: ManualEventCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    return event_service.create_event_manual(session, body, admin)


@router.get("/{event_id}", response_model=EventDetailRead)
def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return event_service.get_event_detail(session, event_id, user)


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    body: EventUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    return event_service.update_event(session, event_id, body, admin)


@router.post("/{event_id}/groups", response_model=GroupDetailRead, status_code=status.HTTP_201_CREATED)
def create_group(
    event_id: int,
    body: GroupCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return event_service.create_group(session, event_id, body)


@router.post("/preview-csv", response_model=CsvPreviewResponse)
@limiter.limit("10/minute")
def preview_csv(
    request: Request,
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
):
    return event_service.preview_csv(file)


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
    return event_service.import_event(session, event_name, file, column_mapping, admin)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    event_service.delete_event(session, event_id, admin)


# ── Event evaluator pool ─────────────────────────────────────────────────────


@router.get("/{event_id}/evaluators", response_model=list[EvaluatorRead])
def list_event_evaluators(
    event_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return event_service.list_event_evaluators(session, event_id)


@router.post("/{event_id}/evaluators", status_code=status.HTTP_201_CREATED)
def add_event_evaluator(
    event_id: int,
    body: EventEvaluatorAdd,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event_service.add_event_evaluator(session, event_id, body.user_id)
    return {"detail": "Evaluator added to event"}


@router.delete("/{event_id}/evaluators/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_evaluator(
    event_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    event_service.remove_event_evaluator(session, event_id, user_id, admin)


# ── Age categories ───────────────────────────────────────────────────────────


@router.get("/{event_id}/age-categories", response_model=list[AgeCategoryRead])
def list_age_categories(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    return event_service.list_age_categories(session, event_id)


@router.post("/{event_id}/age-categories", response_model=AgeCategoryRead, status_code=status.HTTP_201_CREATED)
def create_age_category(
    event_id: int,
    body: AgeCategoryCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return event_service.create_age_category(session, event_id, body)


@router.delete("/{event_id}/age-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_age_category(
    event_id: int,
    category_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    event_service.delete_age_category(session, event_id, category_id)
