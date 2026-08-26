"""Add conversation-bound order verification.

Revision ID: 0003_order_verification
Revises: 0002_staff_rbac
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_order_verification"
down_revision: str | None = "0002_staff_rbac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders", sa.Column("verification_code_hash", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "conversations", sa.Column("verified_order_id", sa.String(length=40), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("conversations", "verified_order_id")
    op.drop_column("orders", "verification_code_hash")
