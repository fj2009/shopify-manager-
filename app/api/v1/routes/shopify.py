import json
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.database import async_session
from app.models import ShopConnection
from app.services.shopify.catalog import sync_catalog
from app.services.shopify.oauth import exchange_code
from app.services.shopify.security import verify_callback_hmac, verify_webhook_signature
from app.worker.queue import enqueue_webhook

router = APIRouter()


@router.get("/install")
async def install(shop: str):
    if not shop.endswith(".myshopify.com"):
        raise HTTPException(status_code=400, detail="Dominio de shop inválido")
    params = urlencode(
        {
            "client_id": settings.SHOPIFY_API_KEY,
            "scope": "read_products,write_orders,read_customers,read_inventory",
            "redirect_uri": f"{settings.SHOPIFY_APP_URL}/api/v1/shopify/callback",
        }
    )
    return RedirectResponse(f"https://{shop}/admin/oauth/authorize?{params}")


@router.get("/callback")
async def callback(request: Request):
    params = dict(request.query_params)
    if not verify_callback_hmac(params):
        raise HTTPException(status_code=401, detail="HMAC inválido")

    shop = params.get("shop", "")
    code = params.get("code", "")
    if not shop or not code:
        raise HTTPException(status_code=400, detail="Faltan parámetros")

    token = await exchange_code(shop, code)

    async with async_session() as session:
        conn = (
            await session.execute(
                select(ShopConnection).where(ShopConnection.shop_domain == shop)
            )
        ).scalar_one_or_none()
        if conn is None:
            conn = ShopConnection(shop_domain=shop, access_token=token)
            session.add(conn)
        else:
            conn.access_token = token
        await session.commit()

    await sync_catalog(shop, token)
    return RedirectResponse(url=settings.APP_HOME_URL)


@router.post("/sync")
async def sync_storefront():
    async with async_session() as session:
        conn = (await session.execute(select(ShopConnection))).scalars().first()
        if conn is None:
            raise HTTPException(status_code=404, detail="No hay tiendas conectadas")
        shop_domain, token = conn.shop_domain, conn.access_token
    total = await sync_catalog(shop_domain, token)
    return {"shop": shop_domain, "products_synced": total}


@router.get("/status")
async def status():
    async with async_session() as session:
        conns = (await session.execute(select(ShopConnection))).scalars().all()
    return [
        {"shop_domain": c.shop_domain, "installed_at": c.installed_at} for c in conns
    ]


@router.post("/webhooks/{topic}")
async def webhook(topic: str, request: Request):
    raw = await request.body()
    if not verify_webhook_signature(raw, request.headers.get("X-Shopify-Hmac-Sha256")):
        raise HTTPException(status_code=401, detail="Firma inválida")
    payload = json.loads(raw)
    await enqueue_webhook(topic=topic, payload=payload)
    return {"queued": topic}