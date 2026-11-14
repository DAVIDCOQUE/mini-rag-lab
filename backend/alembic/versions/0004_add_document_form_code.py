"""add form_code to documents

Revision ID: 0004_document_form_code
Revises: 0003_document_kind
Create Date: 2026-10-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_document_form_code"
down_revision: str | None = "0003_document_kind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Opcional: no todos los formatos traen un codigo impreso.
    op.add_column("documents", sa.Column("form_code", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "form_code")
