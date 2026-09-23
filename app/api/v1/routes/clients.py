from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models import Client

router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.get("")
async def search_clients(
    q: str | None = None,
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Client).limit(limit)
    if q:
        like = f"%{q}%"
        stmt = select(Client).where(
            or_(Client.full_name.ilike(like), Client.email.ilike(like))
        ).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()