from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user
from app.database import get_session
from app.models.diploma_template import DiplomaTemplate
from app.models.event import Event
from app.models.user import User, UserRole
from app.schemas.diploma import DiplomaTemplateCreate, DiplomaTemplateRead, DiplomaTemplateUpdate

router = APIRouter(tags=["diplomas"])


def _get_event_or_404(event_id: int, session: Session) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def _get_template_or_404(event_id: int, session: Session) -> DiplomaTemplate:
    template = session.exec(
        select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id)
    ).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diploma template not found")
    return template


def _to_read(t: DiplomaTemplate) -> DiplomaTemplateRead:
    return DiplomaTemplateRead(
        id=t.id,
        event_id=t.event_id,
        bg_image_url=t.bg_image_url,
        orientation=t.orientation,
        items=t.items or [],
        fonts=t.fonts or [],
        created_at=t.created_at,
    )


@router.get("/events/{event_id}/diploma", response_model=DiplomaTemplateRead)
def get_diploma_template(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    _get_event_or_404(event_id, session)
    return _to_read(_get_template_or_404(event_id, session))


@router.post("/events/{event_id}/diploma", response_model=DiplomaTemplateRead, status_code=status.HTTP_201_CREATED)
def create_diploma_template(
    event_id: int,
    body: DiplomaTemplateCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    _get_event_or_404(event_id, session)

    if session.exec(select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Diploma template already exists for this event")

    template = DiplomaTemplate(
        event_id=event_id,
        bg_image_url=body.bg_image_url,
        orientation=body.orientation,
        items=body.items,
        fonts=body.fonts,
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return _to_read(template)


@router.put("/events/{event_id}/diploma", response_model=DiplomaTemplateRead)
def update_diploma_template(
    event_id: int,
    body: DiplomaTemplateUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    _get_event_or_404(event_id, session)
    template = _get_template_or_404(event_id, session)

    # bg_image_url: None means "clear it", so always apply
    template.bg_image_url = body.bg_image_url
    if body.orientation is not None:
        template.orientation = body.orientation
    if body.items is not None:
        template.items = body.items
    if body.fonts is not None:
        template.fonts = body.fonts

    session.add(template)
    session.commit()
    session.refresh(template)
    return _to_read(template)


@router.delete("/events/{event_id}/diploma", status_code=status.HTTP_204_NO_CONTENT)
def delete_diploma_template(
    event_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    _get_event_or_404(event_id, session)
    template = _get_template_or_404(event_id, session)
    session.delete(template)
    session.commit()
