"""store move analysis details

Revision ID: c1a2b3d4e5f6
Revises: 7094f0900820
Create Date: 2026-10-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7094f0900820"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("move_analyses", sa.Column("san", sa.String(), nullable=True))
    op.add_column("move_analyses", sa.Column("moving_color", sa.String(), nullable=True))
    op.add_column("move_analyses", sa.Column("eval_before_kind", sa.String(), nullable=True))
    op.add_column("move_analyses", sa.Column("eval_before_cp", sa.Integer(), nullable=True))
    op.add_column("move_analyses", sa.Column("eval_before_mate_in", sa.Integer(), nullable=True))
    op.add_column("move_analyses", sa.Column("eval_after_kind", sa.String(), nullable=True))
    op.add_column("move_analyses", sa.Column("eval_after_cp", sa.Integer(), nullable=True))
    op.add_column("move_analyses", sa.Column("eval_after_mate_in", sa.Integer(), nullable=True))
    op.add_column("move_analyses", sa.Column("is_forced", sa.Boolean(), nullable=True))
    op.add_column("move_analyses", sa.Column("analysis_status", sa.String(), nullable=True))
    op.add_column("move_analyses", sa.Column("skipped_reason", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("move_analyses", "skipped_reason")
    op.drop_column("move_analyses", "analysis_status")
    op.drop_column("move_analyses", "is_forced")
    op.drop_column("move_analyses", "eval_after_mate_in")
    op.drop_column("move_analyses", "eval_after_cp")
    op.drop_column("move_analyses", "eval_after_kind")
    op.drop_column("move_analyses", "eval_before_mate_in")
    op.drop_column("move_analyses", "eval_before_cp")
    op.drop_column("move_analyses", "eval_before_kind")
    op.drop_column("move_analyses", "moving_color")
    op.drop_column("move_analyses", "san")
