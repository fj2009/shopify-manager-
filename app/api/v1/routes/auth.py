from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Seller
from app.schemas.auth import LoginRequest, RegisterRequest, SellerInfo, TokenResponse

router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


def _token_response(seller: Seller) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(seller.id, seller.role),
        seller=SellerInfo(
            id=seller.id,
            email=seller.email,
            full_name=seller.full_name,
            role=seller.role,
            monthly_target=seller.monthly_target,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    seller = (
        await session.execute(
            select(Seller).where(Seller.email == payload.email.strip().lower())
        )
    ).scalar_one_or_none()
    if seller is None or not seller.password_hash:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not verify_password(payload.password, seller.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return _token_response(seller)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="La contraseña debe tener 8+ caracteres")

    email = payload.email.strip().lower()
    existing = (
        await session.execute(select(Seller).where(Seller.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    seller = Seller(
        email=email,
        full_name=payload.full_name,
        monthly_target=payload.monthly_target,
        password_hash=hash_password(payload.password),
        role="seller",
    )
    session.add(seller)
    await session.commit()
    await session.refresh(seller)
    return _token_response(seller)