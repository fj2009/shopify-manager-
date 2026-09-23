import asyncio
import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models import Product, ProductVariant
from app.services.shopify.client import ShopifyGraphQLClient

logger = logging.getLogger(__name__)

CATALOG_QUERY = """
query Catalog($cursor: String) {
  products(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        title
        handle
        featuredImage { url }
        variants(first: 100) {
          edges { node { id title sku inventoryQuantity } }
        }
      }
    }
  }
}
"""

PRODUCT_QUERY = """
query Product($id: ID!) {
  product(id: $id) {
    id
    title
    handle
    featuredImage { url }
    variants(first: 100) {
      edges { node { id title sku inventoryQuantity } }
    }
  }
}
"""


def _extract(node: dict) -> dict:
    variants = []
    for edge in node.get("variants", {}).get("edges", []):
        variant = edge["node"]
        variants.append(
            {
                "shopify_id": variant["id"],
                "title": variant.get("title") or "",
                "sku": variant.get("sku"),
                "stock": int(variant.get("inventoryQuantity") or 0),
            }
        )
    return {
        "shopify_id": node["id"],
        "title": node.get("title") or "",
        "handle": node.get("handle"),
        "image_url": (node.get("featuredImage") or {}).get("url"),
        "critically_low_stock": any(
            v["stock"] <= settings.LOW_STOCK_THRESHOLD for v in variants
        ),
        "variants": variants,
    }


async def _upsert_product(session, data: dict) -> Product:
    product = (
        await session.execute(
            select(Product).where(Product.shopify_id == data["shopify_id"])
        )
    ).scalar_one_or_none()
    if product is None:
        product = Product(shopify_id=data["shopify_id"])
        session.add(product)

    product.title = data["title"]
    product.handle = data["handle"]
    product.image_url = data["image_url"]
    product.critically_low_stock = data["critically_low_stock"]
    await session.flush()

    incoming = {v["shopify_id"] for v in data["variants"]}
    existing = {
        v.shopify_id: v
        for v in (await session.execute(select(ProductVariant).where(ProductVariant.product_id == product.id))).scalars()
    }
    for variant_id in existing.keys() - incoming:
        await session.delete(existing[variant_id])

    for variant_data in data["variants"]:
        variant = existing.get(variant_data["shopify_id"])
        if variant is None:
            variant = ProductVariant(
                product_id=product.id, shopify_id=variant_data["shopify_id"]
            )
            session.add(variant)
        variant.title = variant_data["title"]
        variant.sku = variant_data["sku"]
        variant.stock = variant_data["stock"]
    await session.flush()
    return product


async def sync_catalog(shop_domain: str, access_token: str) -> int:
    client = ShopifyGraphQLClient(shop_domain, access_token)
    cursor = None
    total = 0
    while True:
        payload = await client.query(CATALOG_QUERY, {"cursor": cursor})
        page = payload["data"]["products"]
        async with async_session() as session:
            for edge in page["edges"]:
                await _upsert_product(session, _extract(edge["node"]))
                total += 1
            await session.commit()
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
        await asyncio.sleep(0.5)
    logger.info("Catálogo sincronizado: %s productos", total)
    return total


async def sync_product(shop_domain: str, access_token: str, product_gid: str) -> None:
    client = ShopifyGraphQLClient(shop_domain, access_token)
    payload = await client.query(PRODUCT_QUERY, {"id": product_gid})
    node = payload["data"]["product"]
    if node is None:
        return
    async with async_session() as session:
        await _upsert_product(session, _extract(node))
        await session.commit()