import httpx

from app.core.config import settings


async def exchange_code(shop_domain: str, code: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"https://{shop_domain}/admin/oauth/access_token",
            data={
                "client_id": settings.SHOPIFY_API_KEY,
                "client_secret": settings.SHOPIFY_API_SECRET,
                "code": code,
            },
        )
    if response.status_code >= 400:
        raise ShopifyOAuthError(response.status_code, response.text)
    return response.json()["access_token"]


class ShopifyOAuthError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        super().__init__(f"OAuth con Shopify falló {status_code}: {body[:500]}")