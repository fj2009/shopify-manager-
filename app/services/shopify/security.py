import base64
import hashlib
import hmac
from urllib.parse import urlencode

from app.core.config import settings


def verify_callback_hmac(params: dict[str, str]) -> bool:
    signature = params.pop("signature", None) or params.pop("hmac", None)
    if not signature:
        return False
    message = urlencode(sorted(params.items()))
    digest = hmac.new(
        settings.SHOPIFY_API_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def verify_webhook_signature(raw_body: bytes, header: str | None) -> bool:
    if not header or not settings.SHOPIFY_API_SECRET:
        return False
    expected = base64.b64encode(
        hmac.new(settings.SHOPIFY_API_SECRET.encode(), raw_body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, header)