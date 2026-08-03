"""create prompt_templates table

Revision ID: 0002_prompt_templates
Revises: 0001_documents
Create Date: 2026-08-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_prompt_templates"
down_revision: str | None = "0001_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_prompt_templates_code", "prompt_templates", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_prompt_templates_code", table_name="prompt_templates")
    op.drop_table("prompt_templates")
