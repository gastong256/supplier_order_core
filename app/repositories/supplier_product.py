import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.supplier_product import SupplierProduct
from app.schemas.supplier_product import SupplierProductCreate, SupplierProductUpdate


class SupplierProductRepository:
    @staticmethod
    async def get(
        session: AsyncSession, supplier_id: uuid.UUID, product_id: uuid.UUID
    ) -> SupplierProduct | None:
        result = await session.execute(
            select(SupplierProduct).where(
                SupplierProduct.supplier_id == supplier_id,
                SupplierProduct.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_for_supplier(
        session: AsyncSession, supplier_id: uuid.UUID
    ) -> list[SupplierProduct]:
        result = await session.execute(
            select(SupplierProduct)
            .where(SupplierProduct.supplier_id == supplier_id)
            .options(selectinload(SupplierProduct.product))
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession, supplier_id: uuid.UUID, data: SupplierProductCreate
    ) -> SupplierProduct:
        sp = SupplierProduct(supplier_id=supplier_id, **data.model_dump())
        session.add(sp)
        await session.flush()
        # reload with product relationship
        result = await session.execute(
            select(SupplierProduct)
            .where(
                SupplierProduct.supplier_id == sp.supplier_id,
                SupplierProduct.product_id == sp.product_id,
            )
            .options(selectinload(SupplierProduct.product))
        )
        return result.scalar_one()

    @staticmethod
    async def update(
        session: AsyncSession, sp: SupplierProduct, data: SupplierProductUpdate
    ) -> SupplierProduct:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(sp, field, value)
        session.add(sp)
        await session.flush()
        result = await session.execute(
            select(SupplierProduct)
            .where(
                SupplierProduct.supplier_id == sp.supplier_id,
                SupplierProduct.product_id == sp.product_id,
            )
            .options(selectinload(SupplierProduct.product))
        )
        return result.scalar_one()

    @staticmethod
    async def delete(session: AsyncSession, sp: SupplierProduct) -> None:
        await session.delete(sp)
        await session.flush()
