import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.supplier import Supplier
from app.models.supplier_product import SupplierProduct
from app.repositories.product import ProductRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.supplier_product import SupplierProductRepository
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.schemas.supplier_product import SupplierProductCreate, SupplierProductUpdate


class SupplierService:
    @staticmethod
    async def list_suppliers(
        db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> list[Supplier]:
        return await SupplierRepository.get_all(db, skip=skip, limit=limit)

    @staticmethod
    async def get_supplier(db: AsyncSession, supplier_id: uuid.UUID) -> Supplier:
        supplier = await SupplierRepository.get_by_id(db, supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier", str(supplier_id))
        return supplier

    @staticmethod
    async def get_supplier_with_products(db: AsyncSession, supplier_id: uuid.UUID) -> Supplier:
        supplier = await SupplierRepository.get_with_products(db, supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier", str(supplier_id))
        return supplier

    @staticmethod
    async def create_supplier(db: AsyncSession, data: SupplierCreate) -> Supplier:
        existing = await SupplierRepository.get_by_name(db, data.name)
        if existing is not None:
            raise ConflictError(f"A supplier named '{data.name}' already exists.")
        return await SupplierRepository.create(db, data)

    @staticmethod
    async def update_supplier(
        db: AsyncSession, supplier_id: uuid.UUID, data: SupplierUpdate
    ) -> Supplier:
        supplier = await SupplierService.get_supplier(db, supplier_id)
        if data.name is not None and data.name != supplier.name:
            existing = await SupplierRepository.get_by_name(db, data.name)
            if existing is not None:
                raise ConflictError(f"A supplier named '{data.name}' already exists.")
        return await SupplierRepository.update(db, supplier, data)

    @staticmethod
    async def delete_supplier(db: AsyncSession, supplier_id: uuid.UUID) -> None:
        supplier = await SupplierService.get_supplier(db, supplier_id)
        await SupplierRepository.delete(db, supplier)

    # ── Supplier-Product management ───────────────────────────────────────────

    @staticmethod
    async def list_supplier_products(
        db: AsyncSession, supplier_id: uuid.UUID
    ) -> list[SupplierProduct]:
        await SupplierService.get_supplier(db, supplier_id)
        return await SupplierProductRepository.get_all_for_supplier(db, supplier_id)

    @staticmethod
    async def add_product_to_supplier(
        db: AsyncSession, supplier_id: uuid.UUID, data: SupplierProductCreate
    ) -> SupplierProduct:
        await SupplierService.get_supplier(db, supplier_id)

        product = await ProductRepository.get_by_id(db, data.product_id)
        if product is None:
            raise NotFoundError("Product", str(data.product_id))

        existing_link = await SupplierProductRepository.get(db, supplier_id, data.product_id)
        if existing_link is not None:
            raise ConflictError(
                f"Product '{data.product_id}' is already linked to this supplier."
            )

        return await SupplierProductRepository.create(db, supplier_id, data)

    @staticmethod
    async def update_supplier_product(
        db: AsyncSession,
        supplier_id: uuid.UUID,
        product_id: uuid.UUID,
        data: SupplierProductUpdate,
    ) -> SupplierProduct:
        await SupplierService.get_supplier(db, supplier_id)
        sp = await SupplierProductRepository.get(db, supplier_id, product_id)
        if sp is None:
            raise NotFoundError(
                "SupplierProduct", f"{supplier_id}/{product_id}"
            )
        return await SupplierProductRepository.update(db, sp, data)

    @staticmethod
    async def remove_product_from_supplier(
        db: AsyncSession, supplier_id: uuid.UUID, product_id: uuid.UUID
    ) -> None:
        await SupplierService.get_supplier(db, supplier_id)
        sp = await SupplierProductRepository.get(db, supplier_id, product_id)
        if sp is None:
            raise NotFoundError(
                "SupplierProduct", f"{supplier_id}/{product_id}"
            )
        await SupplierProductRepository.delete(db, sp)
