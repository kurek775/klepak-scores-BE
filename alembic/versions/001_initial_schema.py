"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="EVALUATOR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    # event
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="DRAFT"),
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_event_name", "event", ["name"])

    # group
    op.create_table(
        "group",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("identifier", sa.String(), nullable=False, server_default=""),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
    )

    # group_evaluator
    op.create_table(
        "group_evaluator",
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("group.id"), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True, nullable=False),
    )

    # participant
    op.create_table(
        "participant",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("group.id"), nullable=False),
    )

    # activity
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("evaluation_type", sa.String(), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # record
    op.create_table(
        "record",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("value_raw", sa.String(), nullable=False),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participant.id"), nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activity.id"), nullable=False),
        sa.Column("evaluator_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("participant_id", "activity_id", name="uq_record_participant_activity"),
    )

    # age_category
    op.create_table(
        "age_category",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_age", sa.Integer(), nullable=False, server_default="999"),
    )

    # diplomatemplate
    op.create_table(
        "diplomatemplate",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("bg_image_url", sa.String(), nullable=True),
        sa.Column("orientation", sa.String(), nullable=False, server_default="PORTRAIT"),
        sa.Column("items", sa.JSON(), nullable=True),
        sa.Column("fonts", sa.JSON(), nullable=True),
        sa.Column("default_font", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_diploma_event"),
    )
    op.create_index("ix_diplomatemplate_event_id", "diplomatemplate", ["event_id"])

    # auditlog
    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("detail", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_auditlog_user_id", "auditlog", ["user_id"])
    op.create_index("ix_auditlog_created_at", "auditlog", ["created_at"])


def downgrade() -> None:
    op.drop_table("auditlog")
    op.drop_table("diplomatemplate")
    op.drop_table("age_category")
    op.drop_table("record")
    op.drop_table("activity")
    op.drop_table("participant")
    op.drop_table("group_evaluator")
    op.drop_table("group")
    op.drop_table("event")
    op.drop_table("user")
