import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)

_storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"
if _storage_uri == "memory://":
    logger.warning(
        "Rate limiter using in-memory storage — not effective behind a load balancer. "
        "Set REDIS_URL for distributed rate limiting."
    )

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri,
)
