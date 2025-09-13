from datetime import datetime, timedelta
from jose import jwt
from .config import settings


def create_app_jwt(
    sub: str,
    is_admin: bool,
    email: str,
    name: str | None,
    picture: str | None,
    crew_id: str | None,
    tour_id: str | None,
    hours: int = 12,
) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "email": email,
        "name": name,
        "crew_id": crew_id,
        "tour_id": tour_id,
        "is_admin": is_admin,
        "picture": picture,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=hours)).timestamp()),
        "iss": "your-app",
        "aud": "your-frontend",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
