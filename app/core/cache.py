from cachetools import TTLCache

# Leaderboard cache: keyed by event_id, 30-second TTL
leaderboard_cache: TTLCache = TTLCache(maxsize=256, ttl=30)
