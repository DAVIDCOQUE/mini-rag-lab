"""create chat_logs

Revision ID: 0007_chat_logs
Revises: 0006_document_public_url
Create Date: 2026-11-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_chat_logs"
down_revision: str | None = "0006_document_public_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("turn", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("route", sa.String(length=20), nullable=False),
        sa.Column("router", sa.String(length=20), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("top_score", sa.Float(), nullable=True),
        sa.Column("no_answer", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("offered_forms", sa.String(length=255), nullable=True),
        sa.Column("delivered_forms", sa.String(length=255), nullable=True),
        sa.Column("prompt_code", sa.String(length=64), nullable=True),
        sa.Column("routing_ms", sa.Float(), nullable=True),
        sa.Column("retrieval_ms", sa.Float(), nullable=True),
        sa.Column("generation_ms", sa.Float(), nullable=True),
        sa.Column("total_ms", sa.Float(), nullable=False),
    )
    op.create_index("ix_chat_logs_created_at", "chat_logs", ["created_at"])
    op.create_index("ix_chat_logs_conversation_id", "chat_logs", ["conversation_id"])
    op.create_index("ix_chat_logs_route", "chat_logs", ["route"])
    op.create_index("ix_chat_logs_no_answer", "chat_logs", ["no_answer"])


def downgrade() -> None:
    op.drop_table("chat_logs")
