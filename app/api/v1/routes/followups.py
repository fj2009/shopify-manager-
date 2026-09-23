from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models import Client, FollowUp, Product, ProductVariant, Sale
from app.schemas.followups import FollowUpItem, FollowUpUpdate

router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.get("", response_model=list[FollowUpItem])
async def list_followups(
    status: str = Query("pending"),
    horizon_days: int = Query(3, ge=0, le=60),
    session: AsyncSession = Depends(get_session),
):
    horizon = date.today() + timedelta(days=horizon_days)
    stmt = (
        select(FollowUp, Client, Sale, ProductVariant, Product)
        .join(Client, Client.id == FollowUp.client_id)
        .join(Sale, Sale.id == FollowUp.sale_id)
        .outerjoin(ProductVariant, ProductVariant.id == Sale.product_variant_id)
        .outerjoin(Product, Product.id == ProductVariant.product_id)
        .where(FollowUp.status == status, FollowUp.planned_on <= horizon)
        .order_by(FollowUp.planned_on.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        FollowUpItem(
            id=f.id,
            sale_id=f.sale_id,
            client_name=client.full_name,
            client_email=client.email,
            client_phone=client.phone,
            product_title=product.title if product else None,
            variant_title=variant.title if variant else None,
            sold_at=sale.sold_at,
            planned_on=f.planned_on,
            status=f.status,
            note=f.note,
            overdue=f.planned_on < date.today(),
        )
        for f, client, sale, variant, product in rows
    ]


@router.patch("/{followup_id}", response_model=FollowUpItem)
async def update_followup(
    followup_id: int,
    payload: FollowUpUpdate,
    session: AsyncSession = Depends(get_session),
):
    followup = await session.get(FollowUp, followup_id)
    if followup is None:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")

    followup.status = payload.status
    if payload.note is not None:
        followup.note = payload.note
    await session.commit()

    return await _item(session, followup)


async def _item(session: AsyncSession, f: FollowUp) -> FollowUpItem:
    row = (
        await session.execute(
            select(FollowUp, Client, Sale, ProductVariant, Product)
            .join(Client, Client.id == FollowUp.client_id)
            .join(Sale, Sale.id == FollowUp.sale_id)
            .outerjoin(ProductVariant, ProductVariant.id == Sale.product_variant_id)
            .outerjoin(Product, Product.id == ProductVariant.product_id)
            .where(FollowUp.id == f.id)
        )
    ).one()
    followup, client, sale, variant, product = row
    return FollowUpItem(
        id=followup.id,
        sale_id=followup.sale_id,
        client_name=client.full_name,
        client_email=client.email,
        client_phone=client.phone,
        product_title=product.title if product else None,
        variant_title=variant.title if variant else None,
        sold_at=sale.sold_at,
        planned_on=followup.planned_on,
        status=followup.status,
        note=followup.note,
        overdue=followup.planned_on < date.today(),
    )