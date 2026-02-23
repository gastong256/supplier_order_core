import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.supplier import Supplier


class SupplierProduct(TimestampMixin, Base):
    __tablename__ = "supplier_products"
    __table_args__ = (
        PrimaryKeyConstraint("supplier_id", "product_id", name="pk_supplier_products"),
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    minimum_quantity: Mapped[float] = mapped_column(nullable=False, default=0.0)
    optimal_quantity: Mapped[float] = mapped_column(nullable=False, default=0.0)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="supplier_products")
    product: Mapped["Product"] = relationship("Product", back_populates="supplier_products")
