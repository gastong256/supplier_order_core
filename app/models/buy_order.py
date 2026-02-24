import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.buy_order_item import BuyOrderItem
    from app.models.supplier import Supplier


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SENT = "SENT"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


# Valid status transitions: {from_status: set of allowed to_status}
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.DRAFT: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SENT, OrderStatus.CANCELLED},
    OrderStatus.SENT: {OrderStatus.RECEIVED, OrderStatus.CANCELLED},
    OrderStatus.RECEIVED: set(),
    OrderStatus.CANCELLED: set(),
}


class BuyOrder(BaseModel):
    __tablename__ = "buy_orders"

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        String(20), nullable=False, default=OrderStatus.DRAFT
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    total: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=4), nullable=False, default=Decimal("0")
    )

    supplier: Mapped["Supplier"] = relationship("Supplier")
    items: Mapped[list["BuyOrderItem"]] = relationship(
        "BuyOrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
