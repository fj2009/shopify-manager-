import asyncio
import json
import logging
from decimal import Decimal

from sqlalchemy import select

from app.core.database import async_session
from app.models import (
    Client,
    ProductVariant,
    Sale,
    ShopConnection,
    WorkshopNote,
)
from app.services.shopify.orders import push_sale_to_shopify
from app.worker.followup import scheduling_loop
from app.worker.queue import OUTBOUND_QUEUE, WEBHOOK_QUEUE, client as redis_client

logger = logging.getLogger("shopify.worker")

STATUS_BY_FINANCIAL = {"paid": "paid", "pending": "pending", "authorized": "pending"}


async def handle_order_created(payload: dict) -> None:
    order_id = str(payload["id"])
    customer = payload.get("customer") or {}
    email = customer.get("email")
    if not email:
        return

    async with async_session() as session:
        existing = (
            await session.execute(
                select(Sale).where(Sale.shopify_order_id == order_id)
            )
        ).scalar_one_or_none()
        if existing is not None:
            return

        client = (
            await session.execute(select(Client).where(Client.email == email))
        ).scalar_one_or_none()
        if client is None:
            client = Client(
                shopify_id=str(customer.get("id")) if customer.get("id") else None,
                email=email,
                full_name=(
                    f"{customer.get('first_name', '')} {customer.get('last_name', '')}"
                ).strip()
                or None,
                phone=customer.get("phone"),
            )
            session.add(client)
            await session.flush()

        status = STATUS_BY_FINANCIAL.get(payload.get("financial_status"), "pending")
        for item in payload.get("line_items", []):
            variant_gid = (
                f"gid://shopify/ProductVariant/{item['variant_id']}"
                if item.get("variant_id")
                else None
            )
            variant = None
            if variant_gid:
                variant = (
                    await session.execute(
                        select(ProductVariant).where(
                            ProductVariant.shopify_id == variant_gid
                        )
                    )
                ).scalar_one_or_none()

            quantity = int(item.get("quantity", 1))
            unit_price = Decimal(str(item.get("price", "0")))
            session.add(
                Sale(
                    shopify_order_id=order_id,
                    client=client,
                    product_variant_id=variant.id if variant else None,
                    quantity=quantity,
                    unit_price=unit_price,
                    total=unit_price * quantity,
                    status=status,
                )
            )
        await session.commit()
        logger.info("Pedido %s reflejado", order_id)


async def handle_product_updated(payload: dict) -> None:
    from app.services.shopify.catalog import sync_product

    product_gid = payload.get("admin_graphql_api_id") or payload.get("id")
    async with async_session() as session:
        conn = (await session.execute(select(ShopConnection))).scalars().first()
    if conn is None or product_gid is None:
        return
    await sync_product(conn.shop_domain, conn.access_token, product_gid)


async def handle_push_sale(sale_id: int) -> None:
    async with async_session() as session:
        sale = await session.get(Sale, sale_id)
        if sale is None or sale.shopify_order_id:
            return
        client = await session.get(Client, sale.client_id)
        if client is None:
            return
        conn = (await session.execute(select(ShopConnection))).scalars().first()
        if conn is None:
            return
        variant = (
            await session.get(ProductVariant, sale.product_variant_id)
            if sale.product_variant_id
            else None
        )
        if variant is None:
            return

        notes = (
            await session.execute(
                select(WorkshopNote).where(WorkshopNote.sale_id == sale.id)
            )
        ).scalars().all()
        specifications = [n.specification for n in notes]
        if sale.seller_id:
            specifications.append(f"Vendedor ID: {sale.seller_id}")
        note = "\n".join(specifications) or None

        order_gid = await push_sale_to_shopify(
            conn.shop_domain,
            conn.access_token,
            email=client.email,
            line_items=[{"variantId": variant.shopify_id, "quantity": sale.quantity}],
            note=note,
        )
        sale.shopify_order_id = order_gid
        await session.commit()
        logger.info("Venta %s enviada a Shopify (%s)", sale.id, order_gid)


WEBHOOK_HANDLERS = {
    "orders/create": handle_order_created,
    "orders/updated": handle_order_created,
    "products/update": handle_product_updated,
}


async def process_webhook(raw: str) -> None:
    item = json.loads(raw)
    handler = WEBHOOK_HANDLERS.get(item.get("topic"))
    if handler is None:
        logger.info("Topic sin handler: %s", item.get("topic"))
        return
    await handler(item.get("payload") or {})


async def process_outbound(item: dict) -> None:
    kind = item.get("kind")
    if kind == "push_sale":
        await handle_push_sale(int(item["sale_id"]))
    else:
        logger.info("Outbound sin handler: %s", kind)


async def run() -> None:
    logger.info("Worker iniciado")
    asyncio.create_task(scheduling_loop())
    while True:
        popped = await redis_client.blpop([WEBHOOK_QUEUE, OUTBOUND_QUEUE], timeout=1)
        if popped is None:
            continue
        queue_name, raw = popped
        try:
            if queue_name == OUTBOUND_QUEUE:
                await process_outbound(json.loads(raw))
            else:
                await process_webhook(raw)
        except Exception:
            logger.exception("Error procesando mensaje de %s", queue_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())