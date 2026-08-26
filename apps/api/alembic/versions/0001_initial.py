"""Create the TokoMate MVP schema.

Revision ID: 0001_initial
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

locale_enum = sa.Enum("id", "en", name="locale", native_enum=False)
conversation_status_enum = sa.Enum(
    "ai_active",
    "escalated",
    "human_active",
    "resolved",
    name="conversationstatus",
    native_enum=False,
)
sender_enum = sa.Enum("customer", "assistant", "agent", "system", name="sender", native_enum=False)
priority_enum = sa.Enum("low", "medium", "high", name="priority", native_enum=False)
escalation_status_enum = sa.Enum("open", "taken_over", name="escalationstatus", native_enum=False)
summary_status_enum = sa.Enum("pending", "ready", "failed", name="summarystatus", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_table(
        "product_variants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("size", sa.String(length=40), nullable=False),
        sa.Column("color", sa.String(length=60), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "size", "color"),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("courier", sa.String(length=80), nullable=True),
        sa.Column("tracking_number", sa.String(length=120), nullable=True),
        sa.Column("estimated_delivery", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "faq",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("locale", locale_enum, nullable=False),
        sa.Column("question", sa.String(length=240), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("locale", locale_enum, nullable=False),
        sa.Column("status", conversation_status_enum, nullable=False),
        sa.Column("detected_order_id", sa.String(length=40), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sender", sender_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])
    op.create_table(
        "escalations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.String(length=40), nullable=True),
        sa.Column("issue_category", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("status", escalation_status_enum, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("summary_status", summary_status_enum, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("taken_over_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id"),
    )
    op.create_index("ix_escalations_conversation_id", "escalations", ["conversation_id"])
    op.create_index("ix_escalations_created_at", "escalations", ["created_at"])


def downgrade() -> None:
    op.drop_table("escalations")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("faq")
    op.drop_table("orders")
    op.drop_table("product_variants")
    op.drop_table("products")
