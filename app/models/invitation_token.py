from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.models.user import UserRole


class InvitationToken(SQLModel, table=True):
    __tablename__ = "invitation_token"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    role: UserRole
    token_hash: str = Field(index=True)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    used: bool = Field(default=False)
    invited_by: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
