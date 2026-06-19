"""
Product models for MIOS.

Represents product/item entities in the manufacturing system.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from shared.models.base import Base, TimestampMixin, SoftDeleteMixin


class Product(Base, TimestampMixin, SoftDeleteMixin):
    """Product entity model."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    
    # Unit of measure
    unit_of_measure = Column(String(50), default="piece")
    
    # Pricing
    standard_cost = Column(Numeric(12, 4), default=0)
    list_price = Column(Numeric(12, 4), default=0)
    
    # Inventory tracking
    track_inventory = Column(Boolean, default=True)
    reorder_point = Column(Numeric(12, 2), default=0)
    reorder_quantity = Column(Numeric(12, 2), default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    
    # Relationships
    bom_headers = relationship("BOMHeader", back_populates="product")
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    @staticmethod
    def generate_code(value: int) -> str:
        """Generate product code."""
        return f"PROD-{value:06d}"


class BOMHeader(Base, TimestampMixin, SoftDeleteMixin):
    """Bill of Materials header model."""
    
    __tablename__ = "bom_headers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="bom_headers")
    items = relationship("BOMItem", back_populates="bom_header")
    
    def __repr__(self) -> str:
        return f"<BOMHeader(id={self.id}, code='{self.code}', version={self.version})>"
    
    @staticmethod
    def generate_code(value: int) -> str:
        """Generate BOM code."""
        return f"BOM-{value:06d}"


class BOMItem(Base, TimestampMixin, SoftDeleteMixin):
    """Bill of Materials item model."""
    
    __tablename__ = "bom_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_header_id = Column(Integer, ForeignKey("bom_headers.id"), nullable=False)
    component_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Numeric(12, 4), nullable=False, default=1)
    unit_of_measure = Column(String(50), default="piece")
    sequence_number = Column(Integer, default=1)
    
    # Relationships
    bom_header = relationship("BOMHeader", back_populates="items")
    component_product = relationship("Product")
    
    def __repr__(self) -> str:
        return f"<BOMItem(id={self.id}, bom_id={self.bom_header_id}, qty={self.quantity})>"

