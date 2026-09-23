import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.database import Base, async_session, engine
from app.core.security import hash_password
from app.models import Product, ProductVariant, Seller


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        sellers = (await session.execute(select(Seller))).scalars().all()
        demo_sellers = [
            Seller(
                email="ana@tienda.com",
                full_name="Ana Torres",
                monthly_target=40,
                password_hash=hash_password("secret123"),
            ),
            Seller(
                email="luis@tienda.com",
                full_name="Luis Perez",
                monthly_target=50,
                password_hash=hash_password("secret123"),
            ),
        ]
        if not sellers:
            session.add_all(demo_sellers)
        else:
            for seller in sellers:
                if not seller.password_hash:
                    seller.password_hash = hash_password("secret123")

        products = (await session.execute(select(Product))).scalars().all()
        if not products:
            session.add_all(
                [
                    Product(
                        shopify_id="gid://shopify/Product/1001",
                        title="Lampara de Mesa Nordica",
                        handle="lampara-mesa-nordica",
                        variants=[
                            ProductVariant(
                                shopify_id="gid://shopify/ProductVariant/2001",
                                title="Blanca / E27",
                                sku="LMN-01",
                                stock=24,
                                price=Decimal("1299.00"),
                            )
                        ],
                    ),
                    Product(
                        shopify_id="gid://shopify/Product/1002",
                        title="Lampara de Pie Minimalista",
                        handle="lampara-pie-minimalista",
                        variants=[
                            ProductVariant(
                                shopify_id="gid://shopify/ProductVariant/2002",
                                title="Negra / 2m",
                                sku="LPM-02",
                                stock=5,
                                price=Decimal("2499.00"),
                            )
                        ],
                    ),
                    Product(
                        shopify_id="gid://shopify/Product/1003",
                        title="Lampara Colgante Industrial",
                        handle="lampara-colgante-industrial",
                        critically_low_stock=True,
                        variants=[
                            ProductVariant(
                                shopify_id="gid://shopify/ProductVariant/2003",
                                title="Gris / E27",
                                sku="LCI-03",
                                stock=2,
                                price=Decimal("1899.00"),
                            )
                        ],
                    ),
                ]
            )

        await session.commit()

    print("Seed completado")


if __name__ == "__main__":
    asyncio.run(seed())