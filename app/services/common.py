"""Shared service helpers."""

import logging

from sqlmodel import Session, SQLModel

from app.core.exceptions import NotFoundException
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


def get_or_404(session: Session, model: type[SQLModel], entity_id: int, label: str | None = None) -> SQLModel:
    """Fetch an entity by primary key or raise NotFoundException."""
    entity = session.get(model, entity_id)
    if entity is None:
        raise NotFoundException(label or model.__name__, entity_id)
    return entity


def invalidate_leaderboard_cache(event_id: int | None) -> None:
    """Drop the cached leaderboard for an event after a structural change."""
    if event_id is None:
        return
    try:
        if redis_client:
            redis_client.delete(f"leaderboard:{event_id}")
    except Exception:
        logger.warning("Failed to invalidate leaderboard cache for event %s", event_id)
