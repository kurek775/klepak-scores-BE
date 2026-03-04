from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.dependencies import get_current_active_user, get_current_admin
from app.database import get_session
from app.models.user import User
from app.schemas.diploma import DiplomaTemplateCreate, DiplomaTemplateRead, DiplomaTemplateUpdate
from app.services import diploma_service

router = APIRouter(tags=["diplomas"])


@router.get("/events/{event_id}/diplomas", response_model=list[DiplomaTemplateRead])
def list_diploma_templates(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    return diploma_service.list_diploma_templates(session, event_id)


@router.post("/events/{event_id}/diplomas", response_model=DiplomaTemplateRead, status_code=status.HTTP_201_CREATED)
def create_diploma_template(
    event_id: int,
    body: DiplomaTemplateCreate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return diploma_service.create_diploma_template(session, event_id, body)


@router.get("/events/{event_id}/diplomas/{template_id}", response_model=DiplomaTemplateRead)
def get_diploma_template(
    event_id: int,
    template_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    return diploma_service.get_diploma_template(session, event_id, template_id)


@router.put("/events/{event_id}/diplomas/{template_id}", response_model=DiplomaTemplateRead)
def update_diploma_template(
    event_id: int,
    template_id: int,
    body: DiplomaTemplateUpdate,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    return diploma_service.update_diploma_template(session, event_id, template_id, body)


@router.delete("/events/{event_id}/diplomas/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diploma_template(
    event_id: int,
    template_id: int,
    session: Session = Depends(get_session),
    _admin: User = Depends(get_current_admin),
):
    diploma_service.delete_diploma_template(session, event_id, template_id)
