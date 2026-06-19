"""
Pydantic schemas for product API.

Request/response validation for product endpoints.
"""

from typing import Optional, List
from pydantic import Field, ConfigDict
from datetime import datetime

from shared.schemas.common import BaseSchema


class ProductBase(BaseSchema):
    """Base product schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Categorization
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    
    # Unit of measure
    unit_of_measure: Optional[str] = Field(default="piece", max_length=50)
    
    # Pricing
    standard_cost: Optional[float] = Field(default=0, ge=0)
    list_price: Optional[float] = Field(default=0, ge=0)
    
    # Inventory tracking
    track_inventory: Optional[bool] = True
    reorder_point: Optional[float] = Field(default=0, ge=0)
    reorder_quantity: Optional[float] = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    
    pass


class ProductUpdate(BaseSchema):
    """Schema for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    standard_cost: Optional[float] = Field(None, ge=0)
    list_price: Optional[float] = Field(None, ge=0)
    track_inventory: Optional[bool] = None
    reorder_point: Optional[float] = Field(None, ge=0)
    reorder_quantity: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    
    id: int
    code: str
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BOMItemBase(BaseSchema):
    """Base BOM item schema."""
    
    component_product_id: int
    quantity: float = Field(..., gt=0)
    unit_of_measure: Optional[str] = Field(default="piece", max_length=50)
    sequence_number: Optional[int] = Field(default=1, ge=1)


class BOMItemCreate(BOMItemBase):
    """Schema for creating a BOM item."""
    
    pass


class BOMItemResponse(BOMItemBase):
    """Schema for BOM item response."""
    
    id: int
    bom_header_id: int
    
    model_config = ConfigDict(from_attributes=True)


class BOMHeaderBase(BaseSchema):
    """Base BOM header schema."""
    
    product_id: int
    version: Optional[int] = Field(default=1, ge=1)
    is_active: Optional[bool] = True
    effective_date: Optional[datetime] = None


class BOMHeaderCreate(BOMHeaderBase):
    """Schema for creating a BOM header."""
    
    items: List[BOMItemCreate] = []


class BOMHeaderResponse(BOMHeaderBase):
    """Schema for BOM header response."""
    
    id: int
    code: str
    created_at: datetime
    updated_at: datetime
    items: List[BOMItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

