from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class InvitationToken(SQLModel, table=True):
    __tablename__ = "invitation_token"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    role: str  # "EVALUATOR" or "SUPER_ADMIN"
    token_hash: str = Field(index=True)
    expires_at: datetime
    used: bool = Field(default=False)
    invited_by: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
