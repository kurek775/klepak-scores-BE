"""Invitation token table and SUPER_ADMIN role

Revision ID: 006
Revises: 005
Create Date: 2026-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invitation_token",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("invited_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_invitation_token_email", "invitation_token", ["email"])
    op.create_index("ix_invitation_token_token_hash", "invitation_token", ["token_hash"])
    op.create_index("ix_invitation_token_invited_by", "invitation_token", ["invited_by"])


def downgrade() -> None:
    op.drop_index("ix_invitation_token_invited_by", table_name="invitation_token")
    op.drop_index("ix_invitation_token_token_hash", table_name="invitation_token")
    op.drop_index("ix_invitation_token_email", table_name="invitation_token")
    op.drop_table("invitation_token")
