"""Event evaluator pool

Revision ID: 003
Revises: 002
Create Date: 2026-02-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_evaluator",
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True, nullable=False),
    )

    # Backfill: ensure every existing group evaluator also has an event-level assignment
    op.execute(
        'INSERT INTO event_evaluator (event_id, user_id) '
        'SELECT DISTINCT g.event_id, ge.user_id '
        'FROM group_evaluator ge '
        'JOIN "group" g ON ge.group_id = g.id '
        'ON CONFLICT DO NOTHING'
    )


def downgrade() -> None:
    op.drop_table("event_evaluator")
