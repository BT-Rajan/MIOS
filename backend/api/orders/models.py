"""
Order models for MIOS.

Defines order entities with workflow states, versioning, and audit support.
All financial data is immutable once recorded.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    Enum as SQLEnum,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.core.database import Base


class OrderStatus(str, Enum):
    """Order workflow states - explicit state machine."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class OrderPriority(str, Enum):
    """Order priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Order(Base):
    """
    Customer order entity.
    
    Supports complete workflow tracking with immutable history.
    Never hard deleted - uses soft delete pattern.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Order identification
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Workflow state
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.DRAFT, nullable=False, index=True
    )
    priority: Mapped[OrderPriority] = mapped_column(
        SQLEnum(OrderPriority), default=OrderPriority.NORMAL, nullable=False
    )
    
    # Dates
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    required_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    promised_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Financial data (immutable once order is submitted)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Shipping information
    shipping_address_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("addresses.id"), nullable=True
    )
    billing_address_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("addresses.id"), nullable=True
    )
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    
    # Audit fields
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    shipping_address = relationship("Address", foreign_keys=[shipping_address_id])
    billing_address = relationship("Address", foreign_keys=[billing_address_id])
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    rejector = relationship("User", foreign_keys=[rejected_by])

    __table_args__ = (
        Index("idx_order_customer_status", "customer_id", "status"),
        Index("idx_order_date", "order_date"),
        Index("idx_required_date", "required_date"),
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number} - {self.status.value}>"

    def calculate_totals(self) -> None:
        """Recalculate order totals from items."""
        self.subtotal = sum(item.line_total for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount + self.shipping_cost


class OrderItem(Base):
    """
    Order line item entity.
    
    Immutable once order is submitted.
    Contains snapshot of product data at time of order.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Product reference
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Product snapshot (immutable after order submission)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Quantities and pricing
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_shipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Production tracking
    production_status: Mapped[str] = mapped_column(String(50), default="pending")
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    __table_args__ = (Index("idx_order_item_product", "order_id", "product_id"),)

    def __repr__(self) -> str:
        return f"<OrderItem {self.product_code} x {self.quantity_ordered}>"

    def calculate_line_total(self) -> None:
        """Calculate line total with discount."""
        base_total = Decimal(self.quantity_ordered) * self.unit_price
        discount = base_total * (self.discount_percent / Decimal("100"))
        self.line_total = base_total - discount


class OrderComment(Base):
    """Order comments/notes for communication tracking."""

    __tablename__ = "order_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    order = relationship("Order")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<OrderComment {self.id} for Order {self.order_id}>"
