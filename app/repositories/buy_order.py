import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.buy_order import BuyOrder, OrderStatus
from app.models.buy_order_item import BuyOrderItem
from app.models.supplier import Supplier
from app.schemas.buy_order import BuyOrderCreate, BuyOrderUpdate


class BuyOrderRepository:
    @staticmethod
    async def get_all(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        supplier_id: uuid.UUID | None = None,
        status: OrderStatus | None = None,
    ) -> list[BuyOrder]:
        stmt = (
            select(BuyOrder)
            .options(selectinload(BuyOrder.supplier))
            .offset(skip)
            .limit(limit)
        )
        if supplier_id is not None:
            stmt = stmt.where(BuyOrder.supplier_id == supplier_id)
        if status is not None:
            stmt = stmt.where(BuyOrder.status == status)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: uuid.UUID) -> BuyOrder | None:
        result = await session.execute(
            select(BuyOrder)
            .where(BuyOrder.id == order_id)
            .options(selectinload(BuyOrder.supplier))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_with_items(session: AsyncSession, order_id: uuid.UUID) -> BuyOrder | None:
        result = await session.execute(
            select(BuyOrder)
            .where(BuyOrder.id == order_id)
            .options(
                selectinload(BuyOrder.supplier),
                selectinload(BuyOrder.items).selectinload(BuyOrderItem.product),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, data: BuyOrderCreate) -> BuyOrder:
        order = BuyOrder(
            supplier_id=data.supplier_id,
            notes=data.notes,
            status=OrderStatus.DRAFT,
            total=Decimal("0"),
        )
        session.add(order)
        await session.flush()
        result = await session.execute(
            select(BuyOrder)
            .where(BuyOrder.id == order.id)
            .options(selectinload(BuyOrder.supplier))
        )
        return result.scalar_one()

    @staticmethod
    async def update(session: AsyncSession, order: BuyOrder, data: BuyOrderUpdate) -> BuyOrder:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(order, field, value)
        session.add(order)
        await session.flush()
        await session.refresh(order)
        return order

    @staticmethod
    async def recalculate_total(session: AsyncSession, order: BuyOrder) -> None:
        result = await session.execute(
            select(func.coalesce(func.sum(BuyOrderItem.subtotal), 0)).where(
                BuyOrderItem.order_id == order.id
            )
        )
        total = result.scalar_one()
        order.total = Decimal(str(total))
        session.add(order)
        await session.flush()

    @staticmethod
    async def delete(session: AsyncSession, order: BuyOrder) -> None:
        await session.delete(order)
        await session.flush()
