"""
Procurement models for MIOS.

Handles purchase requisitions, purchase orders, and supplier management.
All financial data is immutable once approved.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Boolean,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from backend.core.database import Base


class RequisitionStatus(str, enum.Enum):
    """Status for purchase requisitions."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONVERTED = "converted"  # Converted to PO
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status for purchase orders."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SENT_TO_VENDOR = "sent_to_vendor"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PurchaseRequisition(Base):
    """
    Purchase requisition entity.
    
    Internal request for purchasing goods/services.
    Requires approval before conversion to PO.
    """
    __tablename__ = "purchase_requisitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requisition_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Requester info
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    
    # Workflow
    status: Mapped[RequisitionStatus] = mapped_column(
        SQLEnum(RequisitionStatus), 
        default=RequisitionStatus.DRAFT,
        nullable=False
    )
    
    # Financials
    estimated_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Vendor suggestion (optional)
    suggested_vendor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vendors.id"))
    
    # Approval
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent
    required_by_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    items: Mapped[List["PurchaseRequisitionItem"]] = relationship(
        "PurchaseRequisitionItem", 
        back_populates="requisition",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["RequisitionComment"]] = relationship(
        "RequisitionComment",
        back_populates="requisition",
        cascade="all, delete-orphan"
    )
    requester: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[requester_id],
        primaryjoin="PurchaseRequisition.requester_id == User.id"
    )
    suggested_vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor",
        foreign_keys=[suggested_vendor_id]
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="requisition",
        uselist=False
    )


class PurchaseRequisitionItem(Base):
    """
    Line items for purchase requisitions.
    """
    __tablename__ = "purchase_requisition_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requisition_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id"), 
        nullable=False,
        index=True
    )
    
    # Product reference
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Snapshot
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantity
    quantity_requested: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="unit")
    
    # Estimated cost
    estimated_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    estimated_line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    
    # Justification
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition", 
        back_populates="items"
    )
    product: Mapped[Optional["Product"]] = relationship("Product")


class PurchaseOrder(Base):
    """
    Purchase order entity.
    
    Formal order sent to vendor.
    Financial data becomes immutable after approval.
    """
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Link to requisition
    requisition_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("purchase_requisitions.id"), 
        nullable=True,
        index=True
    )
    
    # Vendor
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    
    # Workflow
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        SQLEnum(PurchaseOrderStatus),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False
    )
    
    # Dates
    order_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Financials (immutable after approval)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Shipping
    ship_to_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("addresses.id"), nullable=True)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Approval
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Vendor acknowledgment
    vendor_acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    vendor_confirmation_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    receipts: Mapped[List["GoodsReceipt"]] = relationship(
        "GoodsReceipt",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["POComment"]] = relationship(
        "POComment",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    vendor: Mapped["Vendor"] = relationship("Vendor")
    requisition: Mapped[Optional["PurchaseRequisition"]] = relationship(
        "PurchaseRequisition",
        back_populates="purchase_order"
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by]
    )


class PurchaseOrderItem(Base):
    """
    Line items for purchase orders.
    Financial data is immutable after PO approval.
    """
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True
    )
    
    # Product reference
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vendor_product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantity
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.00"))
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="unit")
    
    # Pricing (immutable after approval)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    
    # Delivery
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="items"
    )
    product: Mapped[Optional["Product"]] = relationship("Product")


class GoodsReceipt(Base):
    """
    Goods receipt entity.
    
    Records actual receipt of goods from a PO.
    Links to inventory movements.
    """
    __tablename__ = "goods_receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True
    )
    
    # Receipt details
    received_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    
    # Receiver
    received_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="received")  # received, inspected, accepted, rejected
    
    # Quality
    quality_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    quality_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="receipts"
    )
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    receiver: Mapped["User"] = relationship("User")
    items: Mapped[List["GoodsReceiptItem"]] = relationship(
        "GoodsReceiptItem",
        back_populates="goods_receipt",
        cascade="all, delete-orphan"
    )


class GoodsReceiptItem(Base):
    """
    Line items for goods receipts.
    """
    __tablename__ = "goods_receipt_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goods_receipt_id: Mapped[int] = mapped_column(
        ForeignKey("goods_receipts.id"),
        nullable=False,
        index=True
    )
    
    po_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("purchase_order_items.id"),
        nullable=True
    )
    
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Quantities
    quantity_expected: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.00"))
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="unit")
    
    # Batch/lot tracking
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_numbers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as string
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    goods_receipt: Mapped["GoodsReceipt"] = relationship(
        "GoodsReceipt",
        back_populates="items"
    )
    po_item: Mapped[Optional["PurchaseOrderItem"]] = relationship("PurchaseOrderItem")
    product: Mapped[Optional["Product"]] = relationship("Product")


class RequisitionComment(Base):
    """Comments on purchase requisitions."""
    __tablename__ = "requisition_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requisition_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requisitions.id"),
        nullable=False,
        index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition",
        back_populates="comments"
    )


class POComment(Base):
    """Comments on purchase orders."""
    __tablename__ = "po_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="comments"
    )
