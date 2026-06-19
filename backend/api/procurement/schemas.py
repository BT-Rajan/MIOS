"""
Pydantic schemas for procurement module.

Provides validation and serialization for API requests/responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RequisitionStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONVERTED = "converted"
    CANCELLED = "cancelled"


class PurchaseOrderStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SENT_TO_VENDOR = "sent_to_vendor"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============== Requisition Item Schemas ==============

class RequisitionItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str = Field(..., min_length=1, max_length=255)
    product_code: Optional[str] = Field(None, max_length=100)
    quantity_requested: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="unit", max_length=50)
    estimated_unit_price: Optional[Decimal] = Field(None, ge=0)
    justification: Optional[str] = Field(None, max_length=2000)


class RequisitionItemCreate(RequisitionItemBase):
    pass


class RequisitionItemResponse(RequisitionItemBase):
    id: int
    requisition_id: int
    estimated_line_total: Decimal
    created_at: datetime
    version: int

    class Config:
        from_attributes = True


# ============== Requisition Schemas ==============

class RequisitionItemInCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity_requested: Decimal
    estimated_unit_price: Optional[Decimal] = None
    justification: Optional[str] = None


class PurchaseRequisitionCreate(BaseModel):
    department_id: Optional[int] = None
    suggested_vendor_id: Optional[int] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    required_by_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=5000)
    items: List[RequisitionItemInCreate] = Field(..., min_length=1)


class PurchaseRequisitionUpdate(BaseModel):
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    required_by_date: Optional[datetime] = None
    notes: Optional[str] = None
    suggested_vendor_id: Optional[int] = None


class PurchaseRequisitionSubmit(BaseModel):
    reason: Optional[str] = None


class PurchaseRequisitionApprove(BaseModel):
    reason: Optional[str] = None


class PurchaseRequisitionReject(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class PurchaseRequisitionResponse(BaseModel):
    id: int
    requisition_number: str
    requester_id: int
    department_id: Optional[int]
    status: RequisitionStatusEnum
    estimated_total: Decimal
    currency: str
    suggested_vendor_id: Optional[int]
    priority: str
    required_by_date: Optional[datetime]
    notes: Optional[str]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    version: int
    items: Optional[List[RequisitionItemResponse]] = None

    class Config:
        from_attributes = True


# ============== PO Item Schemas ==============

class POItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str = Field(..., min_length=1, max_length=255)
    product_code: Optional[str] = Field(None, max_length=100)
    vendor_product_code: Optional[str] = Field(None, max_length=100)
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="unit", max_length=50)
    unit_price: Decimal = Field(..., ge=0)
    expected_delivery_date: Optional[datetime] = None


class POItemCreate(POItemBase):
    pass


class POItemResponse(POItemBase):
    id: int
    purchase_order_id: int
    quantity_received: Decimal
    line_total: Decimal
    created_at: datetime
    version: int

    class Config:
        from_attributes = True


# ============== Purchase Order Schemas ==============

class POItemInCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity_ordered: Decimal
    unit_price: Decimal
    expected_delivery_date: Optional[datetime] = None


class PurchaseOrderCreate(BaseModel):
    requisition_id: Optional[int] = None
    vendor_id: int
    expected_delivery_date: Optional[datetime] = None
    shipping_method: Optional[str] = Field(None, max_length=100)
    ship_to_address_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=5000)
    internal_notes: Optional[str] = Field(None, max_length=5000)
    items: List[POItemInCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    expected_delivery_date: Optional[datetime] = None
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseOrderSubmit(BaseModel):
    reason: Optional[str] = None


class PurchaseOrderApprove(BaseModel):
    reason: Optional[str] = None


class PurchaseOrderSendToVendor(BaseModel):
    vendor_confirmation_number: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: int
    po_number: str
    requisition_id: Optional[int]
    vendor_id: int
    status: PurchaseOrderStatusEnum
    order_date: Optional[datetime]
    expected_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    currency: str
    shipping_method: Optional[str]
    tracking_number: Optional[str]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    vendor_acknowledged_at: Optional[datetime]
    vendor_confirmation_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    version: int
    items: Optional[List[POItemResponse]] = None

    class Config:
        from_attributes = True


# ============== Goods Receipt Schemas ==============

class GoodsReceiptItemCreate(BaseModel):
    po_item_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: str
    quantity_expected: Decimal = Field(..., gt=0)
    quantity_received: Decimal = Field(..., ge=0)
    quantity_rejected: Decimal = Field(default=0, ge=0)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_numbers: Optional[str] = None


class GoodsReceiptCreate(BaseModel):
    purchase_order_id: int
    warehouse_id: int
    received_date: datetime
    quality_check_passed: Optional[bool] = None
    quality_notes: Optional[str] = Field(None, max_length=2000)
    items: List[GoodsReceiptItemCreate] = Field(..., min_length=1)


class GoodsReceiptItemResponse(BaseModel):
    id: int
    goods_receipt_id: int
    po_item_id: Optional[int]
    product_id: Optional[int]
    product_name: str
    quantity_expected: Decimal
    quantity_received: Decimal
    quantity_rejected: Decimal
    batch_number: Optional[str]
    serial_numbers: Optional[str]
    created_at: datetime
    version: int

    class Config:
        from_attributes = True


class GoodsReceiptResponse(BaseModel):
    id: int
    receipt_number: str
    purchase_order_id: int
    received_date: datetime
    warehouse_id: int
    received_by: int
    status: str
    quality_check_passed: Optional[bool]
    quality_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    version: int
    items: Optional[List[GoodsReceiptItemResponse]] = None

    class Config:
        from_attributes = True


# ============== Comment Schemas ==============

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = True


class CommentResponse(BaseModel):
    id: int
    entity_id: int
    author_id: int
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True
