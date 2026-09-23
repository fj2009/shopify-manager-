"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sellers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("monthly_target", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_index("ix_sellers_email", "sellers", ["email"], unique=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shopify_id", sa.String(64), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_clients_shopify_id", "clients", ["shopify_id"], unique=True)
    op.create_index("ix_clients_email", "clients", ["email"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shopify_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("handle", sa.String(255), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("critically_low_stock", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("ix_products_shopify_id", "products", ["shopify_id"], unique=True)
    op.create_index("ix_products_title", "products", ["title"], unique=False)
    op.create_index("ix_products_critically_low_stock", "products", ["critically_low_stock"], unique=False)

    op.create_table(
        "product_variants",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shopify_id", sa.String(64), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(64), nullable=True),
        sa.Column("stock", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_index("ix_product_variants_shopify_id", "product_variants", ["shopify_id"], unique=True)
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"], unique=False)
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"], unique=False)
    op.create_index("ix_product_variants_stock", "product_variants", ["stock"], unique=False)

    op.create_table(
        "sales",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shopify_order_id", sa.String(64), nullable=True),
        sa.Column("seller_id", sa.BigInteger(), sa.ForeignKey("sellers.id"), nullable=False),
        sa.Column("client_id", sa.BigInteger(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("product_variant_id", sa.BigInteger(), sa.ForeignKey("product_variants.id"), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("sold_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sales_shopify_order_id", "sales", ["shopify_order_id"], unique=True)
    op.create_index("ix_sales_seller_id", "sales", ["seller_id"], unique=False)
    op.create_index("ix_sales_client_id", "sales", ["client_id"], unique=False)
    op.create_index("ix_sales_status", "sales", ["status"], unique=False)
    op.create_index("ix_sales_sold_at", "sales", ["sold_at"], unique=False)

    op.create_table(
        "workshop_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("sale_id", sa.BigInteger(), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("specification", sa.Text(), nullable=False),
        sa.Column("internal_only", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workshop_notes_sale_id", "workshop_notes", ["sale_id"], unique=False)


def downgrade() -> None:
    op.drop_table("workshop_notes")
    op.drop_table("sales")
    op.drop_table("product_variants")
    op.drop_table("products")
    op.drop_table("clients")
    op.drop_table("sellers")