"""
Pydantic schemas for customer API.

Request/response validation for customer endpoints.
"""

from typing import Optional
from pydantic import Field, EmailStr, ConfigDict
from datetime import datetime

from shared.schemas.common import BaseSchema


class CustomerBase(BaseSchema):
    """Base customer schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Business
    tax_id: Optional[str] = Field(None, max_length=50)
    credit_limit: Optional[float] = Field(default=0, ge=0)
    payment_terms_days: Optional[int] = Field(default=30, ge=0)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    
    pass


class CustomerUpdate(BaseSchema):
    """Schema for updating a customer."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms_days: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response."""
    
    id: int
    code: str
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
