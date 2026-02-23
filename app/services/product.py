import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    @staticmethod
    async def list_products(
        db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> list[Product]:
        return await ProductRepository.get_all(db, skip=skip, limit=limit)

    @staticmethod
    async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
        product = await ProductRepository.get_by_id(db, product_id)
        if product is None:
            raise NotFoundError("Product", str(product_id))
        return product

    @staticmethod
    async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
        existing = await ProductRepository.get_by_sku(db, data.sku)
        if existing is not None:
            raise ConflictError(f"A product with SKU '{data.sku}' already exists.")
        return await ProductRepository.create(db, data)

    @staticmethod
    async def update_product(
        db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate
    ) -> Product:
        product = await ProductService.get_product(db, product_id)
        if data.sku is not None and data.sku != product.sku:
            existing = await ProductRepository.get_by_sku(db, data.sku)
            if existing is not None:
                raise ConflictError(f"A product with SKU '{data.sku}' already exists.")
        return await ProductRepository.update(db, product, data)

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> None:
        product = await ProductService.get_product(db, product_id)
        await ProductRepository.delete(db, product)
