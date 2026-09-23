import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models import FollowUp, Sale

logger = logging.getLogger("shopify.crm")


async def backfill_followups() -> int:
    """Crea seguimientos pendientes para ventas entregadas sin uno previo."""
    async with async_session() as session:
        delivered = (
            await session.execute(
                select(Sale).where(Sale.status == "delivered")
            )
        ).scalars().all()
        existing = (
            await session.execute(
                select(FollowUp.sale_id).where(FollowUp.status == "pending")
            )
        ).scalars().all()
        existing_ids = set(existing)

        created = 0
        for sale in delivered:
            if sale.id in existing_ids:
                continue
            planned_on = (
                sale.sold_at.date() if sale.sold_at else date.today()
            ) + timedelta(days=settings.FOLLOW_UP_DAYS)
            session.add(
                FollowUp(
                    sale_id=sale.id,
                    client_id=sale.client_id,
                    planned_on=planned_on,
                    status="pending",
                )
            )
            existing_ids.add(sale.id)
            created += 1

        if created:
            await session.commit()
            logger.info("Follow-ups creados: %s", created)
    return created


async def scheduling_loop() -> None:
    logger.info("Gestor de follow-ups iniciado")
    while True:
        try:
            await backfill_followups()
        except Exception:
            logger.exception("Error en backfill de follow-ups")
        await asyncio.sleep(3600)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(backfill_followups())
    print("Backfill de follow-ups completado")