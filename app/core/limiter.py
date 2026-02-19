import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_redis_url = os.getenv("REDIS_URL")
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_redis_url if _redis_url else "memory://",
)
