"""
Inventory models for MIOS.

Handles stock items, warehouses, stock movements, and reservations.
All inventory changes are auditable and traceable.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    Text,
    Enum as SQLEnum,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship, validates
import enum

from backend.shared.models.base import Base, TimestampMixin


class StockMovementType(str, enum.Enum):
    """Types of stock movements."""
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    RESERVATION = "reservation"
    RELEASE = "release"


class Warehouse(Base, TimestampMixin):
    """
    Warehouse/Storage location entity.
    
    Supports multiple warehouses with zones and bins.
    """
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    stock_items = relationship("StockItem", back_populates="warehouse", lazy="select")
    movements = relationship("StockMovement", back_populates="warehouse", lazy="select")
    
    __table_args__ = (
        Index("idx_warehouse_code", "code"),
        Index("idx_warehouse_active", "is_active"),
    )
    
    @validates("code")
    def validate_code(self, key: str, value: str) -> str:
        if not value or len(value.strip()) == 0:
            raise ValueError("Warehouse code is required")
        return value.strip().upper()
    
    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        if not value or len(value.strip()) == 0:
            raise ValueError("Warehouse name is required")
        return value.strip()


class StockItem(Base, TimestampMixin):
    """
    Stock item representing quantity of a product in a warehouse.
    
    Tracks current quantity, reserved quantity, and available quantity.
    """
    __tablename__ = "stock_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity_on_hand = Column(Numeric(18, 6), default=0, nullable=False)
    quantity_reserved = Column(Numeric(18, 6), default=0, nullable=False)
    quantity_available = Column(Numeric(18, 6), default=0, nullable=False)
    unit_cost = Column(Numeric(18, 6), nullable=True)  # Last cost for valuation
    bin_location = Column(String(50), nullable=True)
    last_counted_at = Column(DateTime, nullable=True)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="stock_items")
    product = relationship("Product", back_populates="stock_items")
    movements = relationship("StockMovement", back_populates="stock_item", lazy="select")
    reservations = relationship("StockReservation", back_populates="stock_item", lazy="select")
    
    __table_args__ = (
        Index("idx_stock_item_warehouse_product", "warehouse_id", "product_id", unique=True),
    )
    
    @validates("quantity_on_hand", "quantity_reserved", "quantity_available")
    def validate_quantities(self, key: str, value: Optional[Decimal]) -> Decimal:
        if value is None:
            return Decimal("0")
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    def calculate_available(self) -> Decimal:
        """Calculate available quantity."""
        return self.quantity_on_hand - self.quantity_reserved


class StockMovement(Base, TimestampMixin):
    """
    Immutable record of stock movement.
    
    Every stock change creates a movement record for audit trail.
    """
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    movement_type = Column(SQLEnum(StockMovementType), nullable=False)
    quantity = Column(Numeric(18, 6), nullable=False)
    unit_cost = Column(Numeric(18, 6), nullable=True)
    total_value = Column(Numeric(18, 6), nullable=True)
    reference_type = Column(String(50), nullable=True)  # order, production, etc.
    reference_id = Column(Integer, nullable=True, index=True)
    reason = Column(Text, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="movements")
    stock_item = relationship("StockItem", back_populates="movements")
    product = relationship("Product")
    
    __table_args__ = (
        Index("idx_movement_reference", "reference_type", "reference_id"),
        Index("idx_movement_date", "created_at"),
    )
    
    @validates("quantity")
    def validate_quantity(self, key: str, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Movement quantity must be positive")
        return value


class StockReservation(Base, TimestampMixin):
    """
    Stock reservation for orders or production.
    
    Reserves inventory for specific purposes without immediate movement.
    """
    __tablename__ = "stock_reservations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    quantity = Column(Numeric(18, 6), nullable=False)
    reference_type = Column(String(50), nullable=False)  # sales_order, production_order
    reference_id = Column(Integer, nullable=False, index=True)
    reference_line_id = Column(Integer, nullable=True)
    status = Column(String(20), default="active", nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    stock_item = relationship("StockItem", back_populates="reservations")
    product = relationship("Product")
    warehouse = relationship("Warehouse")
    
    __table_args__ = (
        Index("idx_reservation_reference", "reference_type", "reference_id"),
        Index("idx_reservation_status", "status"),
    )
    
    @validates("quantity")
    def validate_quantity(self, key: str, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Reservation quantity must be positive")
        return value
