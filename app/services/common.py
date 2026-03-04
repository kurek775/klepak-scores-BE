"""Shared service helpers."""

from sqlmodel import Session, SQLModel

from app.core.exceptions import NotFoundException


def get_or_404(session: Session, model: type[SQLModel], entity_id: int, label: str | None = None) -> SQLModel:
    """Fetch an entity by primary key or raise NotFoundException."""
    entity = session.get(model, entity_id)
    if entity is None:
        raise NotFoundException(label or model.__name__, entity_id)
    return entity
