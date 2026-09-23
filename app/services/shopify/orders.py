from app.services.shopify.client import ShopifyGraphQLClient, ShopifyAPIError

DRAFT_ORDER_MUTATION = """
mutation DraftOrderCreate($input: DraftOrderInput!) {
  draftOrderCreate(input: $input) {
    draftOrder { id }
    userErrors { field message }
  }
}
"""


async def push_sale_to_shopify(
    shop_domain: str,
    access_token: str,
    *,
    email: str | None,
    line_items: list[dict],
    note: str | None = None,
) -> str:
    client = ShopifyGraphQLClient(shop_domain, access_token)
    payload = await client.query(
        DRAFT_ORDER_MUTATION,
        {
            "input": {
                "email": email,
                "note": note,
                "lineItems": line_items,
            }
        },
    )
    data = payload["data"]["draftOrderCreate"]
    errors = data.get("userErrors") or []
    if errors:
        raise ShopifyAPIError(422, "\n".join(f"{e.get('field')}: {e.get('message')}" for e in errors))
    return data["draftOrder"]["id"]