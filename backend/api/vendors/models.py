"""
Vendor models for MIOS.

Represents vendor/supplier entities in the manufacturing system.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric
from sqlalchemy.orm import relationship

from backend.shared.models.base import Base, TimestampMixin, SoftDeleteMixin


class Vendor(Base, TimestampMixin, SoftDeleteMixin):
    """Vendor/Supplier entity model."""
    
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    
    # Address fields
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business fields
    tax_id = Column(String(50), nullable=True)
    payment_terms_days = Column(Integer, default=30)
    minimum_order_value = Column(Numeric(12, 2), default=0)
    
    # Rating and performance
    rating = Column(Numeric(3, 2), default=0.0)  # 0-5 scale
    is_preferred = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    
    def __repr__(self) -> str:
        return f"<Vendor(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    @staticmethod
    def generate_code(value: int) -> str:
        """Generate vendor code."""
        return f"VEND-{value:06d}"

