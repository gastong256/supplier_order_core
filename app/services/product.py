import csv
import io
import uuid

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import (
    ImportRowStatus,
    ProductCreate,
    ProductImportResult,
    ProductImportRowResult,
    ProductUpdate,
)

logger = get_logger(__name__)


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

    # ── CSV import ────────────────────────────────────────────────────────────

    _REQUIRED_HEADERS = {"name", "sku"}
    _OPTIONAL_HEADERS = {"description", "unit", "stock"}

    @staticmethod
    async def import_from_csv(db: AsyncSession, content: bytes) -> ProductImportResult:
        # Decode and strip BOM
        text = content.decode("utf-8-sig").strip()

        reader = csv.DictReader(io.StringIO(text))

        # Normalize header names (lowercase + strip)
        if reader.fieldnames is None:
            raise ValidationError("CSV file is empty or has no headers.")
        normalized_headers = {h.strip().lower() for h in reader.fieldnames}

        missing = ProductService._REQUIRED_HEADERS - normalized_headers
        if missing:
            raise ValidationError(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}."
            )

        rows: list[ProductImportRowResult] = []
        imported = updated = errors = 0

        for row_num, raw_row in enumerate(reader, start=1):
            # Normalize keys and strip values
            row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items()}

            # Skip completely empty rows
            if not any(row.values()):
                continue

            sku_raw = row.get("sku")
            name_raw = row.get("name")

            try:
                data = ProductCreate(
                    name=name_raw or "",
                    sku=sku_raw or "",
                    description=row.get("description") or None,
                    unit=row.get("unit") or "pcs",
                    stock=float(row.get("stock") or 0),
                )
            except (PydanticValidationError, ValueError) as exc:
                reason = "; ".join(
                    f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()
                ) if isinstance(exc, PydanticValidationError) else str(exc)
                rows.append(ProductImportRowResult(
                    row=row_num,
                    status=ImportRowStatus.ERROR,
                    sku=sku_raw or None,
                    name=name_raw or None,
                    reason=reason,
                ))
                errors += 1
                continue

            try:
                existing = await ProductRepository.get_by_sku(db, data.sku)
                if existing is not None:
                    await ProductRepository.update(
                        db, existing,
                        ProductUpdate(
                            name=data.name,
                            description=data.description,
                            unit=data.unit,
                            stock=data.stock,
                        ),
                    )
                    rows.append(ProductImportRowResult(
                        row=row_num,
                        status=ImportRowStatus.UPDATED,
                        sku=data.sku,
                        name=data.name,
                    ))
                    updated += 1
                else:
                    await ProductRepository.create(db, data)
                    rows.append(ProductImportRowResult(
                        row=row_num,
                        status=ImportRowStatus.IMPORTED,
                        sku=data.sku,
                        name=data.name,
                    ))
                    imported += 1

            except Exception as exc:
                logger.error("CSV import DB error", row=row_num, sku=sku_raw, error=str(exc))
                rows.append(ProductImportRowResult(
                    row=row_num,
                    status=ImportRowStatus.ERROR,
                    sku=sku_raw or None,
                    name=name_raw or None,
                    reason=f"Database error: {exc}",
                ))
                errors += 1

        return ProductImportResult(
            total_rows=len(rows),
            imported=imported,
            updated=updated,
            errors=errors,
            rows=rows,
        )
