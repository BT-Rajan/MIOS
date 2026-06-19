"""
Inventory schemas for MIOS.

Pydantic schemas for request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class StockMovementType(str, Enum):
    """Types of stock movements."""
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    RESERVATION = "reservation"
    RELEASE = "release"


# Warehouse Schemas
class WarehouseBase(BaseModel):
    """Base warehouse schema."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_default: bool = False
    
    @validator("code")
    def validate_code(cls, v: str) -> str:
        return v.strip().upper()
    
    @validator("name")
    def validate_name(cls, v: str) -> str:
        return v.strip()


class WarehouseCreate(WarehouseBase):
    """Schema for creating a warehouse."""
    pass


class WarehouseUpdate(BaseModel):
    """Schema for updating a warehouse."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    
    @validator("name")
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v


class WarehouseResponse(WarehouseBase):
    """Schema for warehouse response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Stock Item Schemas
class StockItemBase(BaseModel):
    """Base stock item schema."""
    product_id: int
    warehouse_id: int
    quantity_on_hand: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_reserved: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_available: Decimal = Field(default=Decimal("0"), ge=0)
    unit_cost: Optional[Decimal] = None
    bin_location: Optional[str] = Field(None, max_length=50)


class StockItemCreate(StockItemBase):
    """Schema for creating a stock item."""
    pass


class StockItemUpdate(BaseModel):
    """Schema for updating a stock item."""
    quantity_on_hand: Optional[Decimal] = Field(None, ge=0)
    quantity_reserved: Optional[Decimal] = Field(None, ge=0)
    quantity_available: Optional[Decimal] = Field(None, ge=0)
    unit_cost: Optional[Decimal] = None
    bin_location: Optional[str] = None
    last_counted_at: Optional[datetime] = None


class StockItemResponse(StockItemBase):
    """Schema for stock item response."""
    id: int
    created_at: datetime
    updated_at: datetime
    available_quantity: Decimal
    
    class Config:
        from_attributes = True


# Stock Movement Schemas
class StockMovementBase(BaseModel):
    """Base stock movement schema."""
    product_id: int
    warehouse_id: int
    movement_type: StockMovementType
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Optional[Decimal] = None
    reason: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class StockMovementCreate(StockMovementBase):
    """Schema for creating a stock movement."""
    pass


class StockMovementResponse(StockMovementBase):
    """Schema for stock movement response."""
    id: int
    total_value: Optional[Decimal] = None
    performed_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Stock Reservation Schemas
class StockReservationBase(BaseModel):
    """Base stock reservation schema."""
    product_id: int
    warehouse_id: int
    quantity: Decimal = Field(..., gt=0)
    reference_type: str
    reference_id: int
    reference_line_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class StockReservationCreate(StockReservationBase):
    """Schema for creating a stock reservation."""
    pass


class StockReservationUpdate(BaseModel):
    """Schema for updating a stock reservation."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class StockReservationResponse(StockReservationBase):
    """Schema for stock reservation response."""
    id: int
    stock_item_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: int
    
    class Config:
        from_attributes = True


# Inventory Summary Schema
class InventorySummary(BaseModel):
    """Schema for inventory summary."""
    product_id: int
    product_name: str
    product_sku: str
    total_on_hand: Decimal
    total_reserved: Decimal
    total_available: Decimal
    warehouse_quantities: List[dict]
