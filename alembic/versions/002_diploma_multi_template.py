"""Multiple diploma templates per event

Revision ID: 002
Revises: 001
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_diploma_event", "diplomatemplate", type_="unique")
    op.add_column(
        "diplomatemplate",
        sa.Column("name", sa.String(), nullable=False, server_default="Default"),
    )


def downgrade() -> None:
    op.drop_column("diplomatemplate", "name")
    op.create_unique_constraint("uq_diploma_event", "diplomatemplate", ["event_id"])
