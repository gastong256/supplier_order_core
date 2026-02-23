import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class SupplierProductCreate(BaseModel):
    product_id: uuid.UUID
    minimum_quantity: float = Field(..., ge=0)
    optimal_quantity: float = Field(..., ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)


class SupplierProductUpdate(BaseModel):
    minimum_quantity: float | None = Field(default=None, ge=0)
    optimal_quantity: float | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)


class SupplierProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supplier_id: uuid.UUID
    product_id: uuid.UUID
    minimum_quantity: float
    optimal_quantity: float
    unit_price: Decimal | None
    created_at: datetime
    updated_at: datetime
    product: ProductResponse
