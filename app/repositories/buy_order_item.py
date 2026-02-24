import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.buy_order_item import BuyOrderItem


class BuyOrderItemRepository:
    @staticmethod
    async def get(
        session: AsyncSession, order_id: uuid.UUID, product_id: uuid.UUID
    ) -> BuyOrderItem | None:
        result = await session.execute(
            select(BuyOrderItem).where(
                BuyOrderItem.order_id == order_id,
                BuyOrderItem.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_for_order(
        session: AsyncSession, order_id: uuid.UUID
    ) -> list[BuyOrderItem]:
        result = await session.execute(
            select(BuyOrderItem)
            .where(BuyOrderItem.order_id == order_id)
            .options(selectinload(BuyOrderItem.product))
        )
        return list(result.scalars().all())

    @staticmethod
    async def _reload(session: AsyncSession, item: BuyOrderItem) -> BuyOrderItem:
        result = await session.execute(
            select(BuyOrderItem)
            .where(
                BuyOrderItem.order_id == item.order_id,
                BuyOrderItem.product_id == item.product_id,
            )
            .options(selectinload(BuyOrderItem.product))
        )
        return result.scalar_one()

    @staticmethod
    async def create(
        session: AsyncSession,
        order_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: float,
        subtotal: Decimal,
    ) -> BuyOrderItem:
        item = BuyOrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=None,
            subtotal=subtotal,
        )
        session.add(item)
        await session.flush()
        return await BuyOrderItemRepository._reload(session, item)

    @staticmethod
    async def update(
        session: AsyncSession,
        item: BuyOrderItem,
        quantity: float,
        unit_price: Decimal | None,
        subtotal: Decimal,
    ) -> BuyOrderItem:
        item.quantity = quantity
        item.unit_price = unit_price
        item.subtotal = subtotal
        session.add(item)
        await session.flush()
        return await BuyOrderItemRepository._reload(session, item)

    @staticmethod
    async def delete(session: AsyncSession, item: BuyOrderItem) -> None:
        await session.delete(item)
        await session.flush()
