from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session
from app.core.deps import get_current_seller
from app.models import (
    Client,
    Product,
    ProductVariant,
    Sale,
    Seller,
    SaleStatusEvent,
    FollowUp,
    WorkshopNote,
)
from app.models.sale import STATUS_FLOW
from app.schemas.sale import (
    ClientCard,
    NoteDeleted,
    ProductCard,
    SaleCreate,
    SaleDetail,
    SaleListItem,
    SaleNoteRead,
    SaleRead,
    SaleStatusUpdate,
    WorkshopNoteCreate,
)
from app.worker.queue import enqueue_sale

router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.post("", response_model=SaleRead, status_code=201)
async def create_sale(
    payload: SaleCreate,
    seller: Seller = Depends(get_current_seller),
    session: AsyncSession = Depends(get_session),
):

    variant = (
        await session.execute(
            select(ProductVariant).where(
                ProductVariant.shopify_id == payload.product_variant_shopify_id
            )
        )
    ).scalar_one_or_none()
    if variant is None:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    if variant.stock < payload.quantity:
        raise HTTPException(status_code=409, detail="Stock insuficiente")

    client = (
        await session.execute(select(Client).where(Client.email == payload.client_email))
    ).scalar_one_or_none()
    if client is None:
        client = Client(email=payload.client_email, full_name=payload.client_email)
        session.add(client)

    sale = Sale(
        seller_id=seller.id,
        client=client,
        product_variant_id=variant.id,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        total=payload.unit_price * payload.quantity,
        status="pending",
    )
    session.add(sale)
    variant.stock -= payload.quantity
    await session.flush()

    product = await session.get(Product, variant.product_id)
    if product is not None:
        await _refresh_critical(session, product)

    if payload.workshop_note:
        session.add(
            WorkshopNote(
                sale_id=sale.id,
                author=seller.email,
                specification=payload.workshop_note,
            )
        )

    await session.commit()
    await session.refresh(sale)
    await enqueue_sale(sale.id)
    return sale


@router.get("", response_model=list[SaleListItem])
async def list_sales(
    seller_id: int | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Sale, Client, ProductVariant, Product)
        .join(Client, Client.id == Sale.client_id)
        .outerjoin(ProductVariant, ProductVariant.id == Sale.product_variant_id)
        .outerjoin(Product, Product.id == ProductVariant.product_id)
        .order_by(Sale.sold_at.desc())
        .limit(limit)
        .offset((page - 1) * limit)
    )
    if seller_id:
        stmt = stmt.where(Sale.seller_id == seller_id)
    if status:
        stmt = stmt.where(Sale.status == status)

    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": sale.id,
            "shopify_order_id": sale.shopify_order_id,
            "quantity": sale.quantity,
            "unit_price": sale.unit_price,
            "total": sale.total,
            "status": sale.status,
            "sold_at": sale.sold_at,
            "client_email": client.email,
            "client_name": client.full_name,
            "product_title": product.title if product else None,
            "variant_title": variant.title if variant else None,
            "sku": variant.sku if variant else None,
            "image_url": product.image_url if product else None,
        }
        for sale, client, variant, product in rows
    ]


@router.get("/{sale_id}", response_model=SaleDetail)
async def get_sale(sale_id: int, session: AsyncSession = Depends(get_session)):
    return await _sale_detail(session, sale_id)


@router.patch("/{sale_id}/status", response_model=SaleDetail)
async def update_status(
    sale_id: int,
    payload: SaleStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    sale = await session.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    if payload.status != sale.status:
        allowed = STATUS_FLOW.get(sale.status, [])
        if payload.status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede pasar de {sale.status} a {payload.status}",
            )

        previous = sale.status
        sale.status = payload.status
        if payload.status == "cancelled" and sale.product_variant_id:
            variant = await session.get(ProductVariant, sale.product_variant_id)
            if variant is not None:
                variant.stock += sale.quantity
                product = await session.get(Product, variant.product_id)
                if product is not None:
                    await _refresh_critical(session, product)
        if payload.status == "delivered":
            existing = (
                await session.execute(
                    select(FollowUp).where(FollowUp.sale_id == sale.id)
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    FollowUp(
                        sale_id=sale.id,
                        client_id=sale.client_id,
                        planned_on=date.today() + timedelta(days=settings.FOLLOW_UP_DAYS),
                        status="pending",
                    )
                )
        session.add(
            SaleStatusEvent(
                sale_id=sale.id,
                from_status=previous,
                to_status=payload.status,
                actor=payload.actor,
            )
        )
        await session.commit()

    return await _sale_detail(session, sale_id)


@router.post("/{sale_id}/notes", response_model=SaleNoteRead, status_code=201)
async def add_note(
    sale_id: int,
    payload: WorkshopNoteCreate,
    session: AsyncSession = Depends(get_session),
):
    sale = await session.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    note = WorkshopNote(
        sale_id=sale.id,
        author=payload.author,
        specification=payload.specification,
        internal_only=payload.internal_only,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/{sale_id}/notes/{note_id}", response_model=NoteDeleted)
async def delete_note(
    sale_id: int,
    note_id: int,
    session: AsyncSession = Depends(get_session),
):
    note = (
        await session.execute(
            select(WorkshopNote).where(
                WorkshopNote.id == note_id,
                WorkshopNote.sale_id == sale_id,
            )
        )
    ).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    await session.delete(note)
    await session.commit()
    return NoteDeleted()


async def _sale_detail(session: AsyncSession, sale_id: int) -> SaleDetail:
    row = (
        await session.execute(
            select(Sale, Client, ProductVariant, Product)
            .join(Client, Client.id == Sale.client_id)
            .outerjoin(ProductVariant, ProductVariant.id == Sale.product_variant_id)
            .outerjoin(Product, Product.id == ProductVariant.product_id)
            .where(Sale.id == sale_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    sale, client, variant, product = row
    notes = (
        await session.execute(
            select(WorkshopNote)
            .where(WorkshopNote.sale_id == sale_id)
            .order_by(WorkshopNote.created_at.desc())
        )
    ).scalars().all()
    events = (
        await session.execute(
            select(SaleStatusEvent)
            .where(SaleStatusEvent.sale_id == sale_id)
            .order_by(SaleStatusEvent.created_at.asc())
        )
    ).scalars().all()

    return SaleDetail(
        sale=sale,
        client=ClientCard(email=client.email, full_name=client.full_name, phone=client.phone),
        product=ProductCard(
            title=product.title if product else "—",
            variant_title=variant.title if variant else None,
            sku=variant.sku if variant else None,
            image_url=product.image_url if product else None,
        ),
        notes=list(notes),
        events=list(events),
    )


async def _refresh_critical(session: AsyncSession, product: Product) -> None:
    variants = (
        await session.execute(
            select(ProductVariant).where(ProductVariant.product_id == product.id)
        )
    ).scalars().all()
    product.critically_low_stock = any(
        v.stock <= settings.LOW_STOCK_THRESHOLD for v in variants
    )