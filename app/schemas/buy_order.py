import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.buy_order import OrderStatus
from app.schemas.product import ProductResponse
from app.schemas.supplier import SupplierResponse


class BuyOrderCreate(BaseModel):
    supplier_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=1000)


class BuyOrderUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class BuyOrderStatusUpdate(BaseModel):
    status: OrderStatus


class BuyOrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: float = Field(..., gt=0)


class BuyOrderItemUpdate(BaseModel):
    quantity: float = Field(..., gt=0)


class BuyOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    quantity: float
    unit_price: Decimal | None
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    product: ProductResponse


class BuyOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    supplier_id: uuid.UUID
    status: OrderStatus
    notes: str | None
    total: Decimal
    created_at: datetime
    updated_at: datetime
    supplier: SupplierResponse


class BuyOrderWithItems(BuyOrderResponse):
    items: list[BuyOrderItemResponse] = []
