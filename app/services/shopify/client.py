import asyncio
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_throttled(payload: dict) -> bool:
    for error in payload.get("errors") or []:
        code = (error.get("extensions") or {}).get("code")
        if code == "THROTTLED":
            return True
    return False


class ShopifyGraphQLClient:
    def __init__(self, shop_domain: str, access_token: str):
        self.endpoint = (
            f"https://{shop_domain}/admin/api/"
            f"{settings.SHOPIFY_API_VERSION}/graphql.json"
        )
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

    async def query(self, query: str, variables: dict | None = None, retries: int = 5):
        for attempt in range(1, retries + 1):
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.endpoint,
                    json={"query": query, "variables": variables or {}},
                    headers=self.headers,
                    follow_redirects=True,
                )

            if response.status_code == 429:
                await self._backoff(response.headers.get("retry-after", "1"))
                continue

            payload = response.json() if response.text else {}
            if _is_throttled(payload):
                await self._backoff(payload["errors"][0]["extensions"].get("retryAfter", "1"))
                continue

            if response.status_code >= 400:
                raise ShopifyAPIError(response.status_code, response.text)

            return payload

        raise ShopifyRateLimitError("limite de llamadas agotado tras varios reintentos")

    @staticmethod
    async def _backoff(seconds: str) -> None:
        wait = float(seconds)
        logger.warning("shopify rate limit, esperando %ss", wait)
        await asyncio.sleep(min(wait, 30))


class ShopifyRateLimitError(Exception):
    pass


class ShopifyAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        super().__init__(f"Shopify respondió {status_code}: {body[:500]}")