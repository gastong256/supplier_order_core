import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import DBSession
from app.models.buy_order import OrderStatus
from app.schemas.buy_order import (
    BuyOrderCreate,
    BuyOrderItemCreate,
    BuyOrderItemResponse,
    BuyOrderItemUpdate,
    BuyOrderResponse,
    BuyOrderStatusUpdate,
    BuyOrderUpdate,
    BuyOrderWithItems,
)
from app.services.buy_order import BuyOrderService

router = APIRouter(tags=["orders"])


@router.get("", response_model=list[BuyOrderResponse])
async def list_orders(
    db: DBSession,
    skip: int = 0,
    limit: int = 20,
    supplier_id: uuid.UUID | None = Query(default=None),
    order_status: OrderStatus | None = Query(default=None, alias="status"),
) -> list[BuyOrderResponse]:
    return await BuyOrderService.list_orders(  # type: ignore[return-value]
        db, skip=skip, limit=limit, supplier_id=supplier_id, status=order_status
    )


@router.post("", response_model=BuyOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(db: DBSession, body: BuyOrderCreate) -> BuyOrderResponse:
    return await BuyOrderService.create_order(db, body)  # type: ignore[return-value]


@router.get("/{order_id}", response_model=BuyOrderWithItems)
async def get_order(db: DBSession, order_id: uuid.UUID) -> BuyOrderWithItems:
    return await BuyOrderService.get_order_with_items(db, order_id)  # type: ignore[return-value]


@router.patch("/{order_id}", response_model=BuyOrderResponse)
async def update_order(
    db: DBSession, order_id: uuid.UUID, body: BuyOrderUpdate
) -> BuyOrderResponse:
    return await BuyOrderService.update_order(db, order_id, body)  # type: ignore[return-value]


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(db: DBSession, order_id: uuid.UUID) -> None:
    await BuyOrderService.delete_order(db, order_id)


@router.patch("/{order_id}/status", response_model=BuyOrderWithItems)
async def transition_order_status(
    db: DBSession, order_id: uuid.UUID, body: BuyOrderStatusUpdate
) -> BuyOrderWithItems:
    return await BuyOrderService.transition_status(db, order_id, body.status)  # type: ignore[return-value]


# ── Order items ───────────────────────────────────────────────────────────────


@router.post(
    "/{order_id}/items",
    response_model=BuyOrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_item(
    db: DBSession, order_id: uuid.UUID, body: BuyOrderItemCreate
) -> BuyOrderItemResponse:
    return await BuyOrderService.add_item(db, order_id, body)  # type: ignore[return-value]


@router.patch("/{order_id}/items/{product_id}", response_model=BuyOrderItemResponse)
async def update_item(
    db: DBSession,
    order_id: uuid.UUID,
    product_id: uuid.UUID,
    body: BuyOrderItemUpdate,
) -> BuyOrderItemResponse:
    return await BuyOrderService.update_item(db, order_id, product_id, body)  # type: ignore[return-value]


@router.delete("/{order_id}/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    db: DBSession, order_id: uuid.UUID, product_id: uuid.UUID
) -> None:
    await BuyOrderService.remove_item(db, order_id, product_id)
