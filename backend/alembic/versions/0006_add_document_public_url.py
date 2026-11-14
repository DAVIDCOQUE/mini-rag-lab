"""add public_url and cloud_item_id to documents

Revision ID: 0006_document_public_url
Revises: 0005_assistant_profile
Create Date: 2026-11-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_document_public_url"
down_revision: str | None = "0005_assistant_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("public_url", sa.String(length=1024), nullable=True))
    op.add_column("documents", sa.Column("cloud_item_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "cloud_item_id")
    op.drop_column("documents", "public_url")
