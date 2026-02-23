import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    @staticmethod
    async def get_all(session: AsyncSession, skip: int = 0, limit: int = 20) -> list[Product]:
        result = await session.execute(select(Product).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, product_id: uuid.UUID) -> Product | None:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_sku(session: AsyncSession, sku: str) -> Product | None:
        result = await session.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        session.add(product)
        await session.flush()
        await session.refresh(product)
        return product

    @staticmethod
    async def update(session: AsyncSession, product: Product, data: ProductUpdate) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        session.add(product)
        await session.flush()
        await session.refresh(product)
        return product

    @staticmethod
    async def delete(session: AsyncSession, product: Product) -> None:
        await session.delete(product)
        await session.flush()
