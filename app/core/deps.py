import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decode_token
from app.models import Seller

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_seller(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Seller:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    async with async_session() as session:
        seller = await session.get(Seller, int(payload["sub"]))
    if seller is None:
        raise HTTPException(status_code=401, detail="Vendedor no encontrado")
    return seller


def require_role(role: str):
    async def dependency(seller: Seller = Depends(get_current_seller)) -> Seller:
        if seller.role != role:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return seller

    return dependency