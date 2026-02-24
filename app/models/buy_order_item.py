import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.buy_order import BuyOrder
    from app.models.product import Product


class BuyOrderItem(BaseModel):
    __tablename__ = "buy_order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_buy_order_items_order_product"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buy_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=4), nullable=False, default=Decimal("0")
    )

    order: Mapped["BuyOrder"] = relationship("BuyOrder", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
