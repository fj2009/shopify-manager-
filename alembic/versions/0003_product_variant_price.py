"""product_variants.price

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product_variants",
        sa.Column(
            "price", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("product_variants", "price")