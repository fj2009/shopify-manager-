from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models import Product, ProductVariant, Sale, Seller
from app.schemas.dashboard import (
    CriticalItem,
    DashboardOverview,
    DashboardToday,
    SellerProgress,
    SellerRow,
    TopProduct,
    TrendPoint,
)

router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def scalar(session: AsyncSession, stmt):
    return (await session.execute(stmt)).scalar() or 0


@router.get("/today", response_model=DashboardToday)
async def dashboard_today(session: AsyncSession = Depends(get_session)):
    sellers = (await session.execute(select(Seller))).scalars().all()

    sellers_rows: list[SellerProgress] = []
    for seller in sellers:
        units = (
            await session.execute(
                select(func.coalesce(func.sum(Sale.quantity), 0)).where(
                    Sale.seller_id == seller.id,
                    func.date(Sale.sold_at)
                    >= date.today().replace(day=1),
                    func.date(Sale.sold_at) <= date.today(),
                )
            )
        ).scalar() or 0
        progress = round(units / seller.monthly_target * 100, 1) if seller.monthly_target else 0
        sellers_rows.append(SellerProgress(seller=seller.full_name, progress=progress))

    sales_today = (
        await session.execute(
            select(func.count(Sale.id)).where(func.date(Sale.sold_at) == date.today())
        )
    ).scalar() or 0

    critical_stock = (
        await session.execute(
            select(func.count(Product.id)).where(Product.critically_low_stock.is_(True))
        )
    ).scalar() or 0

    return DashboardToday(
        sales_today=sales_today,
        sellers=sellers_rows,
        critical_stock=critical_stock,
    )


@router.get("/overview", response_model=DashboardOverview)
async def overview(session: AsyncSession = Depends(get_session)):
    today = date.today()
    month_start = today.replace(day=1)
    two_weeks_ago = today - timedelta(days=13)
    active = Sale.status != "cancelled"

    sales_today = await scalar(
        session,
        select(func.count(Sale.id)).where(func.date(Sale.sold_at) == today, active),
    )
    revenue_today = await scalar(
        session,
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            func.date(Sale.sold_at) == today, active
        ),
    )
    sales_month = await scalar(
        session,
        select(func.count(Sale.id)).where(Sale.sold_at >= month_start, active),
    )
    revenue_month = await scalar(
        session,
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.sold_at >= month_start, active
        ),
    )

    sellers = (await session.execute(select(Seller))).scalars().all()
    seller_rows: list[SellerRow] = []
    for seller in sellers:
        units = await scalar(
            session,
            select(func.coalesce(func.sum(Sale.quantity), 0)).where(
                Sale.seller_id == seller.id,
                Sale.sold_at >= month_start,
                active,
            ),
        )
        progress = round(units / seller.monthly_target * 100, 1) if seller.monthly_target else 0
        seller_rows.append(
            SellerRow(seller=seller.full_name, units=units, progress=progress)
        )
    seller_rows.sort(key=lambda r: r.progress, reverse=True)

    top_stmt = (
        select(
            Product.title,
            func.coalesce(func.sum(Sale.quantity), 0).label("units"),
            func.coalesce(func.sum(Sale.total), 0).label("revenue"),
        )
        .join(ProductVariant, ProductVariant.id == Sale.product_variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .where(Sale.sold_at >= month_start, active)
        .group_by(Product.title)
        .order_by(func.sum(Sale.quantity).desc())
        .limit(3)
    )
    top_products = [
        TopProduct(title=title, units=units, revenue=revenue)
        for title, units, revenue in (await session.execute(top_stmt)).all()
    ]

    crit_stmt = (
        select(Product.title, ProductVariant.title, ProductVariant.stock)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .where(Product.critically_low_stock.is_(True))
        .order_by(ProductVariant.stock.asc())
    )
    critical_stock = [
        CriticalItem(product_title=title, variant_title=variant_title, stock=stock)
        for title, variant_title, stock in (await session.execute(crit_stmt)).all()
    ]

    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    trend_map: dict[date, dict] = {d: {"units": 0, "revenue": Decimal("0")} for d in days}
    real = (
        await session.execute(
            select(
                func.date(Sale.sold_at),
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.total), 0),
            )
            .where(Sale.sold_at >= two_weeks_ago, active)
            .group_by(func.date(Sale.sold_at))
        )
    ).all()
    for day, units, revenue in real:
        if day in trend_map:
            trend_map[day] = {"units": units, "revenue": revenue}

    trend = [
        TrendPoint(day=d, units=v["units"], revenue=v["revenue"])
        for d, v in trend_map.items()
    ]

    return DashboardOverview(
        sales_today=sales_today,
        sales_month=sales_month,
        revenue_today=revenue_today,
        revenue_month=revenue_month,
        sellers=seller_rows,
        top_products=top_products,
        critical_stock=critical_stock,
        trend=trend,
    )


@router.get("/top-products")
async def top_products(
    seller_id: int | None = None,
    limit: int = Query(3, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(
            ProductVariant.title,
            func.sum(Sale.quantity).label("units"),
        )
        .join(Sale, Sale.product_variant_id == ProductVariant.id)
        .group_by(ProductVariant.title)
        .order_by(func.sum(Sale.quantity).desc())
        .limit(limit)
    )
    if seller_id:
        stmt = stmt.where(Sale.seller_id == seller_id)
    result = await session.execute(stmt)
    return [{"title": title, "units": units} for title, units in result.all()]