"""Recreate event_evaluator table.

Revision ID: 010
Revises: 009
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_evaluator",
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_event_evaluator_event_id", "event_evaluator", ["event_id"])
    op.create_index("ix_event_evaluator_user_id", "event_evaluator", ["user_id"])

    # Backfill: every user who is assigned to a group in an event
    # should also be in that event's evaluator pool.
    op.execute(
        """
        INSERT INTO event_evaluator (event_id, user_id)
        SELECT DISTINCT g.event_id, ge.user_id
        FROM group_evaluator ge
        JOIN "group" g ON ge.group_id = g.id
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_event_evaluator_user_id", table_name="event_evaluator")
    op.drop_index("ix_event_evaluator_event_id", table_name="event_evaluator")
    op.drop_table("event_evaluator")
