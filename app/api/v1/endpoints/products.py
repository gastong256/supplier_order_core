import uuid

from fastapi import APIRouter, status

from app.api.deps import DBSession
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductService

router = APIRouter(tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: DBSession,
    skip: int = 0,
    limit: int = 20,
) -> list[ProductResponse]:
    return await ProductService.list_products(db, skip=skip, limit=limit)  # type: ignore[return-value]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(db: DBSession, body: ProductCreate) -> ProductResponse:
    return await ProductService.create_product(db, body)  # type: ignore[return-value]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(db: DBSession, product_id: uuid.UUID) -> ProductResponse:
    return await ProductService.get_product(db, product_id)  # type: ignore[return-value]


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    db: DBSession, product_id: uuid.UUID, body: ProductUpdate
) -> ProductResponse:
    return await ProductService.update_product(db, product_id, body)  # type: ignore[return-value]


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(db: DBSession, product_id: uuid.UUID) -> None:
    await ProductService.delete_product(db, product_id)
