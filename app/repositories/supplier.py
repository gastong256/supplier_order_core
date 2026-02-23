import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.supplier import Supplier
from app.models.supplier_product import SupplierProduct
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierRepository:
    @staticmethod
    async def get_all(session: AsyncSession, skip: int = 0, limit: int = 20) -> list[Supplier]:
        result = await session.execute(select(Supplier).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, supplier_id: uuid.UUID) -> Supplier | None:
        result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Supplier | None:
        result = await session.execute(select(Supplier).where(Supplier.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_with_products(
        session: AsyncSession, supplier_id: uuid.UUID
    ) -> Supplier | None:
        result = await session.execute(
            select(Supplier)
            .where(Supplier.id == supplier_id)
            .options(
                selectinload(Supplier.supplier_products).selectinload(SupplierProduct.product)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, data: SupplierCreate) -> Supplier:
        supplier = Supplier(**data.model_dump())
        session.add(supplier)
        await session.flush()
        await session.refresh(supplier)
        return supplier

    @staticmethod
    async def update(session: AsyncSession, supplier: Supplier, data: SupplierUpdate) -> Supplier:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(supplier, field, value)
        session.add(supplier)
        await session.flush()
        await session.refresh(supplier)
        return supplier

    @staticmethod
    async def delete(session: AsyncSession, supplier: Supplier) -> None:
        await session.delete(supplier)
        await session.flush()
