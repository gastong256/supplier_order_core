import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.buy_order import ALLOWED_TRANSITIONS, BuyOrder, OrderStatus
from app.models.buy_order_item import BuyOrderItem
from app.repositories.buy_order import BuyOrderRepository
from app.repositories.buy_order_item import BuyOrderItemRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.supplier_product import SupplierProductRepository
from app.schemas.buy_order import (
    BuyOrderCreate,
    BuyOrderItemCreate,
    BuyOrderItemUpdate,
    BuyOrderUpdate,
)


class BuyOrderService:
    # ── Order CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        supplier_id: uuid.UUID | None = None,
        status: OrderStatus | None = None,
    ) -> list[BuyOrder]:
        return await BuyOrderRepository.get_all(
            db, skip=skip, limit=limit, supplier_id=supplier_id, status=status
        )

    @staticmethod
    async def get_order(db: AsyncSession, order_id: uuid.UUID) -> BuyOrder:
        order = await BuyOrderRepository.get_by_id(db, order_id)
        if order is None:
            raise NotFoundError("BuyOrder", str(order_id))
        return order

    @staticmethod
    async def get_order_with_items(db: AsyncSession, order_id: uuid.UUID) -> BuyOrder:
        order = await BuyOrderRepository.get_with_items(db, order_id)
        if order is None:
            raise NotFoundError("BuyOrder", str(order_id))
        return order

    @staticmethod
    async def create_order(db: AsyncSession, data: BuyOrderCreate) -> BuyOrder:
        supplier = await SupplierRepository.get_by_id(db, data.supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier", str(data.supplier_id))
        return await BuyOrderRepository.create(db, data)

    @staticmethod
    async def update_order(
        db: AsyncSession, order_id: uuid.UUID, data: BuyOrderUpdate
    ) -> BuyOrder:
        order = await BuyOrderService.get_order(db, order_id)
        if order.status in (OrderStatus.RECEIVED, OrderStatus.CANCELLED):
            raise ValidationError(
                f"Cannot edit an order in '{order.status}' status."
            )
        return await BuyOrderRepository.update(db, order, data)

    @staticmethod
    async def delete_order(db: AsyncSession, order_id: uuid.UUID) -> None:
        order = await BuyOrderService.get_order(db, order_id)
        if order.status != OrderStatus.DRAFT:
            raise ValidationError(
                f"Only DRAFT orders can be deleted. Current status: '{order.status}'."
            )
        await BuyOrderRepository.delete(db, order)

    @staticmethod
    async def transition_status(
        db: AsyncSession, order_id: uuid.UUID, new_status: OrderStatus
    ) -> BuyOrder:
        order = await BuyOrderRepository.get_with_items(db, order_id)
        if order is None:
            raise NotFoundError("BuyOrder", str(order_id))

        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise ValidationError(
                f"Cannot transition from '{order.status}' to '{new_status}'."
            )

        # On DRAFT → CONFIRMED: snapshot prices and freeze subtotals
        if order.status == OrderStatus.DRAFT and new_status == OrderStatus.CONFIRMED:
            for item in order.items:
                sp = await SupplierProductRepository.get(db, order.supplier_id, item.product_id)
                snapshot_price = sp.unit_price if sp is not None else None
                item.unit_price = snapshot_price
                item.subtotal = Decimal(str(item.quantity)) * (snapshot_price or Decimal("0"))
                db.add(item)
            await db.flush()
            await BuyOrderRepository.recalculate_total(db, order)

        order.status = new_status
        db.add(order)
        await db.flush()

        return await BuyOrderRepository.get_with_items(db, order_id)  # type: ignore[return-value]

    # ── Item management ───────────────────────────────────────────────────────

    @staticmethod
    async def _assert_draft(order: BuyOrder) -> None:
        if order.status != OrderStatus.DRAFT:
            raise ValidationError(
                f"Items can only be modified on DRAFT orders. Current status: '{order.status}'."
            )

    @staticmethod
    async def add_item(
        db: AsyncSession, order_id: uuid.UUID, data: BuyOrderItemCreate
    ) -> BuyOrderItem:
        order = await BuyOrderService.get_order(db, order_id)
        await BuyOrderService._assert_draft(order)

        sp = await SupplierProductRepository.get(db, order.supplier_id, data.product_id)
        if sp is None:
            raise NotFoundError(
                "SupplierProduct",
                f"Product '{data.product_id}' is not sold by this supplier.",
            )

        if data.quantity < sp.minimum_quantity:
            raise ValidationError(
                f"Quantity {data.quantity} is below the minimum required "
                f"({sp.minimum_quantity}) for this product."
            )

        existing = await BuyOrderItemRepository.get(db, order_id, data.product_id)
        if existing is not None:
            raise ConflictError(
                f"Product '{data.product_id}' is already in this order. Use PATCH to update."
            )

        subtotal = Decimal(str(data.quantity)) * (sp.unit_price or Decimal("0"))
        item = await BuyOrderItemRepository.create(
            db, order_id, data.product_id, data.quantity, subtotal
        )
        await BuyOrderRepository.recalculate_total(db, order)
        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        order_id: uuid.UUID,
        product_id: uuid.UUID,
        data: BuyOrderItemUpdate,
    ) -> BuyOrderItem:
        order = await BuyOrderService.get_order(db, order_id)
        await BuyOrderService._assert_draft(order)

        item = await BuyOrderItemRepository.get(db, order_id, product_id)
        if item is None:
            raise NotFoundError("BuyOrderItem", f"{order_id}/{product_id}")

        sp = await SupplierProductRepository.get(db, order.supplier_id, product_id)
        if sp is None:
            raise NotFoundError(
                "SupplierProduct",
                f"Product '{product_id}' is not sold by this supplier.",
            )

        if data.quantity < sp.minimum_quantity:
            raise ValidationError(
                f"Quantity {data.quantity} is below the minimum required "
                f"({sp.minimum_quantity}) for this product."
            )

        subtotal = Decimal(str(data.quantity)) * (sp.unit_price or Decimal("0"))
        updated = await BuyOrderItemRepository.update(
            db, item, data.quantity, None, subtotal
        )
        await BuyOrderRepository.recalculate_total(db, order)
        return updated

    @staticmethod
    async def remove_item(
        db: AsyncSession, order_id: uuid.UUID, product_id: uuid.UUID
    ) -> None:
        order = await BuyOrderService.get_order(db, order_id)
        await BuyOrderService._assert_draft(order)

        item = await BuyOrderItemRepository.get(db, order_id, product_id)
        if item is None:
            raise NotFoundError("BuyOrderItem", f"{order_id}/{product_id}")

        await BuyOrderItemRepository.delete(db, item)
        await BuyOrderRepository.recalculate_total(db, order)
