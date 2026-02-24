from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "auditlog"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    action: str
    resource_type: str | None = None
    resource_id: int | None = None
    detail: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
