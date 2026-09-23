from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models import Product, ProductVariant

router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.get("/search")
async def search(
    q: str = "",
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Product, ProductVariant)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .order_by(Product.title.asc(), ProductVariant.title.asc())
        .limit(limit)
    )
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.title.ilike(like),
                ProductVariant.title.ilike(like),
                ProductVariant.sku.ilike(like),
            )
        )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "variant_shopify_id": v.shopify_id,
            "product_title": p.title,
            "variant_title": v.title,
            "sku": v.sku,
            "stock": v.stock,
            "price": str(v.price),
            "image_url": p.image_url,
        }
        for p, v in rows
    ]