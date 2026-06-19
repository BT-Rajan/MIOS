"""
Pydantic schemas for Order module.

Provides validation, serialization, and API contracts.
No business logic - only data validation and transformation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, PositiveInt, PositiveDecimal, ConfigDict

from backend.api.orders.models import OrderStatus, OrderPriority


# =============================================================================
# ENUM SCHEMAS
# =============================================================================


class OrderStatusSchema(str, Enum):
    """Order status for API."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class OrderPrioritySchema(str, Enum):
    """Order priority for API."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# =============================================================================
# ORDER ITEM SCHEMAS
# =============================================================================


class OrderItemCreate(BaseModel):
    """Schema for creating an order item."""

    product_id: PositiveInt = Field(..., description="Product ID")
    quantity_ordered: PositiveInt = Field(..., description="Quantity to order")
    unit_price: PositiveDecimal = Field(..., description="Unit price")
    discount_percent: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100, description="Discount percentage"
    )
    notes: Optional[str] = Field(None, max_length=1000)


class OrderItemUpdate(BaseModel):
    """Schema for updating an order item (draft orders only)."""

    quantity_ordered: Optional[PositiveInt] = None
    unit_price: Optional[PositiveDecimal] = None
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=1000)


class OrderItemResponse(BaseModel):
    """Order item response schema."""

    id: int
    order_id: int
    product_id: int
    product_code: str
    product_name: str
    quantity_ordered: int
    quantity_shipped: int
    unit_price: Decimal
    discount_percent: Decimal
    line_total: Decimal
    production_status: str
    batch_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ORDER SCHEMAS
# =============================================================================


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    customer_id: PositiveInt = Field(..., description="Customer ID")
    priority: OrderPrioritySchema = Field(
        default=OrderPrioritySchema.NORMAL, description="Order priority"
    )
    required_date: Optional[datetime] = Field(None, description="Required delivery date")
    shipping_address_id: Optional[PositiveInt] = Field(None, description="Shipping address ID")
    billing_address_id: Optional[PositiveInt] = Field(None, description="Billing address ID")
    shipping_method: Optional[str] = Field(None, max_length=100)
    shipping_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Order line items")


class OrderUpdate(BaseModel):
    """Schema for updating a draft order."""

    customer_id: Optional[PositiveInt] = None
    priority: Optional[OrderPrioritySchema] = None
    required_date: Optional[datetime] = None
    shipping_address_id: Optional[PositiveInt] = None
    billing_address_id: Optional[PositiveInt] = None
    shipping_method: Optional[str] = None
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)


class OrderSubmit(BaseModel):
    """Schema for submitting an order."""

    reason: Optional[str] = Field(None, max_length=500, description="Submission reason")


class OrderApprove(BaseModel):
    """Schema for approving an order."""

    reason: Optional[str] = Field(None, max_length=500, description="Approval reason")


class OrderReject(BaseModel):
    """Schema for rejecting an order."""

    reason: str = Field(..., min_length=1, max_length=500, description="Rejection reason (required)")


class OrderCancel(BaseModel):
    """Schema for cancelling an order."""

    reason: str = Field(..., min_length=1, max_length=500, description="Cancellation reason (required)")


class OrderResponse(BaseModel):
    """Order response schema."""

    id: int
    order_number: str
    customer_id: int
    status: OrderStatusSchema
    priority: OrderPrioritySchema
    order_date: datetime
    required_date: Optional[datetime]
    promised_date: Optional[datetime]
    shipped_date: Optional[datetime]
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str
    shipping_address_id: Optional[int]
    billing_address_id: Optional[int]
    shipping_method: Optional[str]
    shipping_cost: Decimal
    created_by: int
    approved_by: Optional[int]
    rejected_by: Optional[int]
    rejection_reason: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailResponse(OrderResponse):
    """Order response with items and comments."""

    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ORDER COMMENT SCHEMAS
# =============================================================================


class OrderCommentCreate(BaseModel):
    """Schema for adding a comment to an order."""

    comment: str = Field(..., min_length=1, max_length=2000, description="Comment text")
    is_internal: bool = Field(default=True, description="Internal note or customer-visible")


class OrderCommentResponse(BaseModel):
    """Order comment response schema."""

    id: int
    order_id: int
    user_id: int
    comment: str
    is_internal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# QUERY SCHEMAS
# =============================================================================


class OrderQueryParams(BaseModel):
    """Query parameters for listing orders."""

    status: Optional[OrderStatusSchema] = None
    priority: Optional[OrderPrioritySchema] = None
    customer_id: Optional[PositiveInt] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: PositiveInt = Field(default=50, le=200)
    offset: int = Field(default=0, ge=0)


class OrderSummary(BaseModel):
    """Order summary for dashboards."""

    order_number: str
    customer_name: str
    status: OrderStatusSchema
    priority: OrderPrioritySchema
    total_amount: Decimal
    order_date: datetime
    required_date: Optional[datetime]
    is_late: bool

    model_config = ConfigDict(from_attributes=True)
