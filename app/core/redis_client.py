import os

import redis

_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client: redis.Redis = redis.from_url(_redis_url, decode_responses=True)
