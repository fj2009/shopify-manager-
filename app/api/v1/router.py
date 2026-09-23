from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    clients,
    dashboard,
    followups,
    products,
    sales,
    shopify,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["autenticación"])
api_router.include_router(sales.router, prefix="/sales", tags=["ventas"])
api_router.include_router(clients.router, prefix="/clients", tags=["clientes"])
api_router.include_router(products.router, prefix="/products", tags=["productos"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(shopify.router, prefix="/shopify", tags=["shopify"])
api_router.include_router(followups.router, prefix="/followups", tags=["seguimiento"])