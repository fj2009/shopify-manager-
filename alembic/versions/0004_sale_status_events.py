"""sale_status_events

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sale_status_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("sale_id", sa.BigInteger(), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_sale_status_events_sale_id", "sale_status_events", ["sale_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_sale_status_events_sale_id", table_name="sale_status_events")
    op.drop_table("sale_status_events")