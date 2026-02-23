import uuid

from fastapi import APIRouter, status

from app.api.deps import DBSession
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate, SupplierWithProducts
from app.schemas.supplier_product import SupplierProductCreate, SupplierProductResponse, SupplierProductUpdate
from app.services.supplier import SupplierService

router = APIRouter(tags=["suppliers"])


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(
    db: DBSession,
    skip: int = 0,
    limit: int = 20,
) -> list[SupplierResponse]:
    return await SupplierService.list_suppliers(db, skip=skip, limit=limit)  # type: ignore[return-value]


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(db: DBSession, body: SupplierCreate) -> SupplierResponse:
    return await SupplierService.create_supplier(db, body)  # type: ignore[return-value]


@router.get("/{supplier_id}", response_model=SupplierWithProducts)
async def get_supplier(db: DBSession, supplier_id: uuid.UUID) -> SupplierWithProducts:
    return await SupplierService.get_supplier_with_products(db, supplier_id)  # type: ignore[return-value]


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    db: DBSession, supplier_id: uuid.UUID, body: SupplierUpdate
) -> SupplierResponse:
    return await SupplierService.update_supplier(db, supplier_id, body)  # type: ignore[return-value]


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(db: DBSession, supplier_id: uuid.UUID) -> None:
    await SupplierService.delete_supplier(db, supplier_id)


# ── Supplier-Product sub-resource ────────────────────────────────────────────


@router.get("/{supplier_id}/products", response_model=list[SupplierProductResponse])
async def list_supplier_products(
    db: DBSession, supplier_id: uuid.UUID
) -> list[SupplierProductResponse]:
    return await SupplierService.list_supplier_products(db, supplier_id)  # type: ignore[return-value]


@router.post(
    "/{supplier_id}/products",
    response_model=SupplierProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_product_to_supplier(
    db: DBSession, supplier_id: uuid.UUID, body: SupplierProductCreate
) -> SupplierProductResponse:
    return await SupplierService.add_product_to_supplier(db, supplier_id, body)  # type: ignore[return-value]


@router.patch(
    "/{supplier_id}/products/{product_id}", response_model=SupplierProductResponse
)
async def update_supplier_product(
    db: DBSession,
    supplier_id: uuid.UUID,
    product_id: uuid.UUID,
    body: SupplierProductUpdate,
) -> SupplierProductResponse:
    return await SupplierService.update_supplier_product(db, supplier_id, product_id, body)  # type: ignore[return-value]


@router.delete(
    "/{supplier_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_product_from_supplier(
    db: DBSession, supplier_id: uuid.UUID, product_id: uuid.UUID
) -> None:
    await SupplierService.remove_product_from_supplier(db, supplier_id, product_id)
