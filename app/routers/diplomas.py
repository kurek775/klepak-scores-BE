from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user
from app.core.permissions import require_admin
from app.database import get_session
from app.models.diploma_template import DiplomaTemplate
from app.models.event import Event
from app.models.user import User
from app.schemas.diploma import DiplomaTemplateCreate, DiplomaTemplateRead, DiplomaTemplateUpdate

router = APIRouter(tags=["diplomas"])


def _get_event_or_404(event_id: int, session: Session) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def _get_template_or_404(event_id: int, template_id: int, session: Session) -> DiplomaTemplate:
    template = session.exec(
        select(DiplomaTemplate).where(
            DiplomaTemplate.event_id == event_id,
            DiplomaTemplate.id == template_id,
        )
    ).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diploma template not found")
    return template


def _to_read(t: DiplomaTemplate) -> DiplomaTemplateRead:
    return DiplomaTemplateRead(
        id=t.id,
        event_id=t.event_id,
        name=t.name,
        bg_image_url=t.bg_image_url,
        orientation=t.orientation,
        items=t.items or [],
        fonts=t.fonts or [],
        default_font=t.default_font,
        created_at=t.created_at,
    )


@router.get("/events/{event_id}/diplomas", response_model=list[DiplomaTemplateRead])
def list_diploma_templates(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    _get_event_or_404(event_id, session)
    templates = session.exec(
        select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id)
    ).all()
    return [_to_read(t) for t in templates]


@router.post("/events/{event_id}/diplomas", response_model=DiplomaTemplateRead, status_code=status.HTTP_201_CREATED)
def create_diploma_template(
    event_id: int,
    body: DiplomaTemplateCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    require_admin(user)
    _get_event_or_404(event_id, session)

    template = DiplomaTemplate(
        event_id=event_id,
        name=body.name,
        bg_image_url=body.bg_image_url,
        orientation=body.orientation,
        items=body.items,
        fonts=body.fonts,
        default_font=body.default_font,
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return _to_read(template)


@router.get("/events/{event_id}/diplomas/{template_id}", response_model=DiplomaTemplateRead)
def get_diploma_template(
    event_id: int,
    template_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    _get_event_or_404(event_id, session)
    return _to_read(_get_template_or_404(event_id, template_id, session))


@router.put("/events/{event_id}/diplomas/{template_id}", response_model=DiplomaTemplateRead)
def update_diploma_template(
    event_id: int,
    template_id: int,
    body: DiplomaTemplateUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    require_admin(user)
    _get_event_or_404(event_id, session)
    template = _get_template_or_404(event_id, template_id, session)

    if body.name is not None:
        template.name = body.name
    # bg_image_url: None means "clear it", so always apply
    template.bg_image_url = body.bg_image_url
    if body.orientation is not None:
        template.orientation = body.orientation
    if body.items is not None:
        template.items = body.items
    if body.fonts is not None:
        template.fonts = body.fonts
    template.default_font = body.default_font

    session.add(template)
    session.commit()
    session.refresh(template)
    return _to_read(template)


@router.delete("/events/{event_id}/diplomas/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diploma_template(
    event_id: int,
    template_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    require_admin(user)
    _get_event_or_404(event_id, session)
    template = _get_template_or_404(event_id, template_id, session)
    session.delete(template)
    session.commit()
