"""Add DB-level cascade deletes and missing indexes

Revision ID: 007
Revises: 006
Create Date: 2026-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _replace_fk(
    table: str,
    column: str,
    ref_table: str,
    ref_column: str,
    on_delete: str,
    constraint_name: str | None = None,
) -> None:
    """Drop existing FK and recreate with ON DELETE behaviour."""
    fk_name = constraint_name or f"{table}_{column}_fkey"
    op.drop_constraint(fk_name, table, type_="foreignkey")
    op.create_foreign_key(
        fk_name, table, ref_table, [column], [ref_column], ondelete=on_delete,
    )


def upgrade() -> None:
    # ── Make columns nullable for SET NULL cascades ─────────────────────────
    op.alter_column("event", "created_by_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("record", "evaluator_id", existing_type=sa.Integer(), nullable=True)

    # ── ON DELETE CASCADE (parent deletion removes children) ───────────────
    _replace_fk("group", "event_id", "event", "id", "CASCADE")
    _replace_fk("participant", "group_id", "group", "id", "CASCADE")
    _replace_fk("activity", "event_id", "event", "id", "CASCADE")
    _replace_fk("record", "participant_id", "participant", "id", "CASCADE")
    _replace_fk("record", "activity_id", "activity", "id", "CASCADE")
    _replace_fk("age_category", "event_id", "event", "id", "CASCADE")
    _replace_fk("diplomatemplate", "event_id", "event", "id", "CASCADE")
    _replace_fk("group_evaluator", "group_id", "group", "id", "CASCADE")
    _replace_fk("group_evaluator", "user_id", "user", "id", "CASCADE")
    _replace_fk("event_evaluator", "event_id", "event", "id", "CASCADE")
    _replace_fk("event_evaluator", "user_id", "user", "id", "CASCADE")
    _replace_fk("password_reset_token", "user_id", "user", "id", "CASCADE")

    # ── ON DELETE SET NULL (keep row, nullify reference) ───────────────────
    _replace_fk("event", "created_by_id", "user", "id", "SET NULL")
    _replace_fk("record", "evaluator_id", "user", "id", "SET NULL")
    _replace_fk("auditlog", "user_id", "user", "id", "SET NULL")
    _replace_fk("invitation_token", "invited_by", "user", "id", "SET NULL")

    # ── Missing indexes on junction table columns ──────────────────────────
    op.create_index("ix_group_evaluator_group_id", "group_evaluator", ["group_id"])
    op.create_index("ix_group_evaluator_user_id", "group_evaluator", ["user_id"])
    op.create_index("ix_event_evaluator_event_id", "event_evaluator", ["event_id"])
    op.create_index("ix_event_evaluator_user_id", "event_evaluator", ["user_id"])
    op.create_index("ix_event_created_by_id", "event", ["created_by_id"])

    # ── Composite index for leaderboard / bulk upsert hot path ─────────────
    op.create_index(
        "ix_record_activity_participant", "record", ["activity_id", "participant_id"],
    )


def downgrade() -> None:
    # ── Drop new indexes ───────────────────────────────────────────────────
    op.drop_index("ix_record_activity_participant", table_name="record")
    op.drop_index("ix_event_created_by_id", table_name="event")
    op.drop_index("ix_event_evaluator_user_id", table_name="event_evaluator")
    op.drop_index("ix_event_evaluator_event_id", table_name="event_evaluator")
    op.drop_index("ix_group_evaluator_user_id", table_name="group_evaluator")
    op.drop_index("ix_group_evaluator_group_id", table_name="group_evaluator")

    # ── Revert SET NULL → plain FK ─────────────────────────────────────────
    _replace_fk("invitation_token", "invited_by", "user", "id", "NO ACTION")
    _replace_fk("auditlog", "user_id", "user", "id", "NO ACTION")
    _replace_fk("record", "evaluator_id", "user", "id", "NO ACTION")
    _replace_fk("event", "created_by_id", "user", "id", "NO ACTION")

    # ── Revert CASCADE → plain FK ─────────────────────────────────────────
    _replace_fk("password_reset_token", "user_id", "user", "id", "NO ACTION")
    _replace_fk("event_evaluator", "user_id", "user", "id", "NO ACTION")
    _replace_fk("event_evaluator", "event_id", "event", "id", "NO ACTION")
    _replace_fk("group_evaluator", "user_id", "user", "id", "NO ACTION")
    _replace_fk("group_evaluator", "group_id", "group", "id", "NO ACTION")
    _replace_fk("diplomatemplate", "event_id", "event", "id", "NO ACTION")
    _replace_fk("age_category", "event_id", "event", "id", "NO ACTION")
    _replace_fk("record", "activity_id", "activity", "id", "NO ACTION")
    _replace_fk("record", "participant_id", "participant", "id", "NO ACTION")
    _replace_fk("activity", "event_id", "event", "id", "NO ACTION")
    _replace_fk("participant", "group_id", "group", "id", "NO ACTION")
    _replace_fk("group", "event_id", "event", "id", "NO ACTION")

    # ── Restore NOT NULL on columns ────────────────────────────────────────
    op.alter_column("record", "evaluator_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("event", "created_by_id", existing_type=sa.Integer(), nullable=False)
