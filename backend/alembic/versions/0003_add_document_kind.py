"""add kind and description to documents

Revision ID: 0003_document_kind
Revises: 0002_prompt_templates
Create Date: 2026-10-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_document_kind"
down_revision: str | None = "0002_prompt_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Los documentos existentes son todos de informacion: el default los cubre.
    op.add_column(
        "documents",
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="KNOWLEDGE"),
    )
    op.add_column("documents", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "description")
    op.drop_column("documents", "kind")
