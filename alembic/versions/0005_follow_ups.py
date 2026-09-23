"""follow_ups

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("sale_id", sa.BigInteger(), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("client_id", sa.BigInteger(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("planned_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(12), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_follow_ups_sale_id", "follow_ups", ["sale_id"], unique=False)
    op.create_index("ix_follow_ups_client_id", "follow_ups", ["client_id"], unique=False)
    op.create_index("ix_follow_ups_planned_on", "follow_ups", ["planned_on"], unique=False)
    op.create_index("ix_follow_ups_status", "follow_ups", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_follow_ups_status", table_name="follow_ups")
    op.drop_index("ix_follow_ups_planned_on", table_name="follow_ups")
    op.drop_index("ix_follow_ups_client_id", table_name="follow_ups")
    op.drop_index("ix_follow_ups_sale_id", table_name="follow_ups")
    op.drop_table("follow_ups")