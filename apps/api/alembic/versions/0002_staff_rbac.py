"""Add staff users for dashboard RBAC.

Revision ID: 0002_staff_rbac
Revises: 0001_initial
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_staff_rbac"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

staff_role_enum = sa.Enum("agent", "admin", name="staffrole", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "staff_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", staff_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_staff_users_email", "staff_users", ["email"])


def downgrade() -> None:
    op.drop_table("staff_users")
