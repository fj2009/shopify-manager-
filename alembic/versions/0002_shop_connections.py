"""shop_connections + sales.seller_id nullable

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("sales", "seller_id", existing_type=sa.BigInteger(), nullable=True)

    op.create_table(
        "shop_connections",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shop_domain", sa.String(255), nullable=False),
        sa.Column("access_token", sa.String(255), nullable=False),
        sa.Column(
            "installed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_shop_connections_shop_domain", "shop_connections", ["shop_domain"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_shop_connections_shop_domain", table_name="shop_connections")
    op.drop_table("shop_connections")
    op.alter_column("sales", "seller_id", existing_type=sa.BigInteger(), nullable=False)