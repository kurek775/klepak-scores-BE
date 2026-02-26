"""Drop event_evaluator table.

Revision ID: 009
Revises: 008
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_event_evaluator_user_id", table_name="event_evaluator")
    op.drop_index("ix_event_evaluator_event_id", table_name="event_evaluator")
    op.drop_table("event_evaluator")


def downgrade() -> None:
    op.create_table(
        "event_evaluator",
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_event_evaluator_event_id", "event_evaluator", ["event_id"])
    op.create_index("ix_event_evaluator_user_id", "event_evaluator", ["user_id"])
