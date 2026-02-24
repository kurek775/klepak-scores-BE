"""Add missing indexes on foreign key columns

Revision ID: 005
Revises: 004
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_group_event_id", "group", ["event_id"])
    op.create_index("ix_participant_group_id", "participant", ["group_id"])
    op.create_index("ix_activity_event_id", "activity", ["event_id"])
    op.create_index("ix_record_participant_id", "record", ["participant_id"])
    op.create_index("ix_record_activity_id", "record", ["activity_id"])
    op.create_index("ix_record_evaluator_id", "record", ["evaluator_id"])
    op.create_index("ix_age_category_event_id", "age_category", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_age_category_event_id", table_name="age_category")
    op.drop_index("ix_record_evaluator_id", table_name="record")
    op.drop_index("ix_record_activity_id", table_name="record")
    op.drop_index("ix_record_participant_id", table_name="record")
    op.drop_index("ix_activity_event_id", table_name="activity")
    op.drop_index("ix_participant_group_id", table_name="participant")
    op.drop_index("ix_group_event_id", table_name="group")
