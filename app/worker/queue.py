import json

import redis.asyncio as aioredis

from app.core.config import settings

client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

WEBHOOK_QUEUE = "shopify:webhooks"
OUTBOUND_QUEUE = "shopify:outbound"


async def enqueue_webhook(topic: str, payload: dict) -> None:
    await client.rpush(WEBHOOK_QUEUE, json.dumps({"topic": topic, "payload": payload}))


async def enqueue_sale(sale_id: int) -> None:
    await client.rpush(OUTBOUND_QUEUE, json.dumps({"kind": "push_sale", "sale_id": sale_id}))


async def drain_webhooks() -> list[dict]:
    batch: list[dict] = []
    for _ in range(100):
        item = await client.lpop(WEBHOOK_QUEUE)
        if item is None:
            break
        batch.append(json.loads(item))
    return batch