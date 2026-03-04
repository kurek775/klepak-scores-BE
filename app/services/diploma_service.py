"""Diploma domain service — business logic extracted from routers/diplomas.py."""

from sqlmodel import Session, select

from app.core.exceptions import NotFoundException
from app.models.diploma_template import DiplomaTemplate
from app.models.event import Event
from app.schemas.diploma import DiplomaTemplateCreate, DiplomaTemplateRead, DiplomaTemplateUpdate
from app.services.common import get_or_404


def _to_read(t: DiplomaTemplate) -> DiplomaTemplateRead:
    return DiplomaTemplateRead(
        id=t.id, event_id=t.event_id, name=t.name,
        bg_image_url=t.bg_image_url, orientation=t.orientation,
        items=t.items or [], fonts=t.fonts or [],
        default_font=t.default_font, created_at=t.created_at,
    )


def list_diploma_templates(session: Session, event_id: int) -> list[DiplomaTemplateRead]:
    get_or_404(session, Event, event_id, "Event")
    templates = session.exec(select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id)).all()
    return [_to_read(t) for t in templates]


def get_diploma_template(session: Session, event_id: int, template_id: int) -> DiplomaTemplateRead:
    get_or_404(session, Event, event_id, "Event")
    template = session.exec(
        select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id, DiplomaTemplate.id == template_id)
    ).first()
    if not template:
        raise NotFoundException("Diploma template", template_id)
    return _to_read(template)


def create_diploma_template(session: Session, event_id: int, body: DiplomaTemplateCreate) -> DiplomaTemplateRead:
    get_or_404(session, Event, event_id, "Event")
    template = DiplomaTemplate(
        event_id=event_id, name=body.name, bg_image_url=body.bg_image_url,
        orientation=body.orientation, items=body.items, fonts=body.fonts,
        default_font=body.default_font,
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return _to_read(template)


def update_diploma_template(
    session: Session, event_id: int, template_id: int, body: DiplomaTemplateUpdate,
) -> DiplomaTemplateRead:
    get_or_404(session, Event, event_id, "Event")
    template = session.exec(
        select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id, DiplomaTemplate.id == template_id)
    ).first()
    if not template:
        raise NotFoundException("Diploma template", template_id)

    if body.name is not None:
        template.name = body.name
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


def delete_diploma_template(session: Session, event_id: int, template_id: int) -> None:
    get_or_404(session, Event, event_id, "Event")
    template = session.exec(
        select(DiplomaTemplate).where(DiplomaTemplate.event_id == event_id, DiplomaTemplate.id == template_id)
    ).first()
    if not template:
        raise NotFoundException("Diploma template", template_id)
    session.delete(template)
    session.commit()
