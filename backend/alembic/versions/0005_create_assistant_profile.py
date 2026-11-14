"""create assistant_profile table

Revision ID: 0005_assistant_profile
Revises: 0004_document_form_code
Create Date: 2026-10-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_assistant_profile"
down_revision: str | None = "0004_document_form_code"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_profile",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("assistant_name", sa.String(length=60), nullable=False),
        sa.Column("assistant_gender", sa.String(length=20), nullable=False, server_default="FEMININE"),
        sa.Column("institution_name", sa.String(length=150), nullable=True),
        sa.Column("institution_short_name", sa.String(length=30), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("help_office", sa.String(length=150), nullable=True),
        sa.Column("help_location", sa.String(length=255), nullable=True),
        sa.Column("help_hours", sa.String(length=150), nullable=True),
        sa.Column("help_phone", sa.String(length=50), nullable=True),
        sa.Column("help_email", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("assistant_profile")
