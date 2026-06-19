"""
Repository layer for procurement module - Requisitions.

All database operations for purchase requisitions.
No business logic - only data access.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from backend.api.procurement.models import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RequisitionComment,
    RequisitionStatus,
)
from backend.api.procurement.exceptions import (
    RequisitionNotFoundException,
    DuplicateRequisitionNumber,
)


class RequisitionRepository:
    """Data access layer for purchase requisitions."""

    def __init__(self, db: Session):
        self.db = db

    def generate_requisition_number(self) -> str:
        """Generate unique requisition number."""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"PR-{today}-"
        
        stmt = select(func.max(PurchaseRequisition.requisition_number)).where(
            PurchaseRequisition.requisition_number.like(f"{prefix}%")
        )
        result = self.db.execute(stmt).scalar()
        
        if result:
            last_num = int(result.split("-")[-1]) + 1
        else:
            last_num = 1
        
        return f"{prefix}{last_num:04d}"

    def create_requisition(
        self,
        requisition_number: str,
        requester_id: int,
        department_id: Optional[int],
        suggested_vendor_id: Optional[int],
        priority: str,
        required_by_date: Optional[datetime],
        notes: Optional[str],
        items: List[dict]
    ) -> PurchaseRequisition:
        """Create new purchase requisition with items."""
        requisition = PurchaseRequisition(
            requisition_number=requisition_number,
            requester_id=requester_id,
            department_id=department_id,
            suggested_vendor_id=suggested_vendor_id,
            priority=priority,
            required_by_date=required_by_date,
            notes=notes,
            status=RequisitionStatus.DRAFT,
            created_at=datetime.now(),
        )
        
        self.db.add(requisition)
        self.db.flush()
        
        for item_data in items:
            item = PurchaseRequisitionItem(
                requisition_id=requisition.id,
                product_id=item_data.get("product_id"),
                product_name=item_data["product_name"],
                product_code=item_data.get("product_code"),
                quantity_requested=item_data["quantity_requested"],
                unit_of_measure=item_data.get("unit_of_measure", "unit"),
                estimated_unit_price=item_data.get("estimated_unit_price"),
                estimated_line_total=(
                    item_data.get("estimated_unit_price", Decimal("0")) * 
                    item_data["quantity_requested"]
                ),
                justification=item_data.get("justification"),
                created_at=datetime.now(),
            )
            self.db.add(item)
        
        self.db.flush()
        return requisition

    def get_requisition_by_id(
        self, 
        requisition_id: int,
        include_items: bool = False
    ) -> PurchaseRequisition:
        """Get requisition by ID."""
        query = select(PurchaseRequisition).where(
            PurchaseRequisition.id == requisition_id,
            PurchaseRequisition.deleted_at.is_(None)
        )
        
        if include_items:
            query = query.options(joinedload(PurchaseRequisition.items))
        
        result = self.db.execute(query).scalar_one_or_none()
        
        if not result:
            raise RequisitionNotFoundException(requisition_id)
        
        return result

    def get_requisition_by_number(
        self,
        requisition_number: str
    ) -> Optional[PurchaseRequisition]:
        """Get requisition by number."""
        query = select(PurchaseRequisition).where(
            PurchaseRequisition.requisition_number == requisition_number,
            PurchaseRequisition.deleted_at.is_(None)
        )
        return self.db.execute(query).scalar_one_or_none()

    def update_requisition_status(
        self,
        requisition: PurchaseRequisition,
        new_status: RequisitionStatus,
        approved_by: Optional[int] = None
    ) -> PurchaseRequisition:
        """Update requisition status."""
        requisition.status = new_status
        requisition.updated_at = datetime.now()
        
        if new_status == RequisitionStatus.SUBMITTED:
            requisition.submitted_at = datetime.now()
        elif new_status == RequisitionStatus.APPROVED:
            requisition.approved_at = datetime.now()
            requisition.approved_by = approved_by
        elif new_status == RequisitionStatus.REJECTED:
            requisition.approved_at = datetime.now()
            requisition.approved_by = approved_by
        
        return requisition

    def set_requisition_rejection_reason(
        self,
        requisition: PurchaseRequisition,
        reason: str
    ) -> None:
        """Set rejection reason."""
        requisition.rejection_reason = reason
        requisition.updated_at = datetime.now()

    def list_requisitions(
        self,
        status: Optional[RequisitionStatus] = None,
        requester_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[PurchaseRequisition], int]:
        """List requisitions with filters."""
        query = select(PurchaseRequisition).where(
            PurchaseRequisition.deleted_at.is_(None)
        )
        
        if status:
            query = query.where(PurchaseRequisition.status == status)
        if requester_id:
            query = query.where(PurchaseRequisition.requester_id == requester_id)
        
        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_stmt).scalar()
        
        query = query.order_by(PurchaseRequisition.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        results = self.db.execute(query).scalars().all()
        return list(results), total

    def soft_delete_requisition(self, requisition: PurchaseRequisition) -> None:
        """Soft delete requisition."""
        requisition.deleted_at = datetime.now()
        requisition.updated_at = datetime.now()

    def add_requisition_comment(
        self,
        requisition_id: int,
        author_id: int,
        content: str,
        is_internal: bool = True
    ) -> RequisitionComment:
        """Add comment to requisition."""
        comment = RequisitionComment(
            requisition_id=requisition_id,
            author_id=author_id,
            content=content,
            is_internal=is_internal,
            created_at=datetime.now(),
        )
        self.db.add(comment)
        self.db.flush()
        return comment

    # ============== Purchase Order Operations ==============

    def generate_po_number(self) -> str:
        """Generate unique PO number."""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"PO-{today}-"
        
        stmt = select(func.max(PurchaseOrder.po_number)).where(
            PurchaseOrder.po_number.like(f"{prefix}%")
        )
        result = self.db.execute(stmt).scalar()
        
        if result:
            last_num = int(result.split("-")[-1]) + 1
        else:
            last_num = 1
        
        return f"{prefix}{last_num:04d}"

    def create_purchase_order(
        self,
        po_number: str,
        requisition_id: Optional[int],
        vendor_id: int,
        order_date: datetime,
        expected_delivery_date: Optional[datetime],
        shipping_method: Optional[str],
        ship_to_address_id: Optional[int],
        notes: Optional[str],
        internal_notes: Optional[str],
        items: List[dict]
    ) -> PurchaseOrder:
        """Create new purchase order with items."""
        po = PurchaseOrder(
            po_number=po_number,
            requisition_id=requisition_id,
            vendor_id=vendor_id,
            order_date=order_date,
            expected_delivery_date=expected_delivery_date,
            shipping_method=shipping_method,
            ship_to_address_id=ship_to_address_id,
            notes=notes,
            internal_notes=internal_notes,
            status=PurchaseOrderStatus.DRAFT,
            created_at=datetime.now(),
        )
        
        self.db.add(po)
        self.db.flush()
        
        subtotal = Decimal("0.00")
        
        for item_data in items:
            line_total = item_data["unit_price"] * item_data["quantity_ordered"]
            subtotal += line_total
            
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=item_data.get("product_id"),
                product_name=item_data["product_name"],
                product_code=item_data.get("product_code"),
                vendor_product_code=item_data.get("vendor_product_code"),
                quantity_ordered=item_data["quantity_ordered"],
                unit_of_measure=item_data.get("unit_of_measure", "unit"),
                unit_price=item_data["unit_price"],
                line_total=line_total,
                expected_delivery_date=item_data.get("expected_delivery_date"),
                created_at=datetime.now(),
            )
            self.db.add(item)
        
        po.subtotal = subtotal
        po.total_amount = subtotal  # Tax and shipping calculated later
        
        self.db.flush()
        return po

    def get_purchase_order_by_id(
        self,
        po_id: int,
        include_items: bool = False
    ) -> PurchaseOrder:
        """Get PO by ID."""
        query = select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.deleted_at.is_(None)
        )
        
        if include_items:
            query = query.options(joinedload(PurchaseOrder.items))
        
        result = self.db.execute(query).scalar_one_or_none()
        
        if not result:
            raise PurchaseOrderNotFoundException(po_id)
        
        return result

    def get_purchase_order_by_number(
        self,
        po_number: str
    ) -> Optional[PurchaseOrder]:
        """Get PO by number."""
        query = select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_number,
            PurchaseOrder.deleted_at.is_(None)
        )
        return self.db.execute(query).scalar_one_or_none()

    def update_po_status(
        self,
        po: PurchaseOrder,
        new_status: PurchaseOrderStatus,
        approved_by: Optional[int] = None
    ) -> PurchaseOrder:
        """Update PO status."""
        po.status = new_status
        po.updated_at = datetime.now()
        
        if new_status == PurchaseOrderStatus.SUBMITTED:
            po.submitted_at = datetime.now()
        elif new_status == PurchaseOrderStatus.APPROVED:
            po.approved_at = datetime.now()
            po.approved_by = approved_by
        elif new_status == PurchaseOrderStatus.SENT_TO_VENDOR:
            po.order_date = datetime.now()
        
        return po

    def update_po_financials(
        self,
        po: PurchaseOrder,
        tax_amount: Decimal,
        shipping_cost: Decimal
    ) -> None:
        """Update PO financial calculations."""
        po.tax_amount = tax_amount
        po.shipping_cost = shipping_cost
        po.total_amount = po.subtotal + tax_amount + shipping_cost
        po.updated_at = datetime.now()

    def increment_po_item_received(
        self,
        po_item: PurchaseOrderItem,
        quantity_received: Decimal
    ) -> None:
        """Increment received quantity on PO item."""
        po_item.quantity_received += quantity_received
        po_item.updated_at = datetime.now()

    def list_purchase_orders(
        self,
        status: Optional[PurchaseOrderStatus] = None,
        vendor_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[PurchaseOrder], int]:
        """List POs with filters."""
        query = select(PurchaseOrder).where(
            PurchaseOrder.deleted_at.is_(None)
        )
        
        if status:
            query = query.where(PurchaseOrder.status == status)
        if vendor_id:
            query = query.where(PurchaseOrder.vendor_id == vendor_id)
        
        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_stmt).scalar()
        
        query = query.order_by(PurchaseOrder.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        results = self.db.execute(query).scalars().all()
        return list(results), total

    def soft_delete_purchase_order(self, po: PurchaseOrder) -> None:
        """Soft delete PO."""
        po.deleted_at = datetime.now()
        po.updated_at = datetime.now()

    # ============== Goods Receipt Operations ==============

    def generate_receipt_number(self) -> str:
        """Generate unique receipt number."""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"GR-{today}-"
        
        stmt = select(func.max(GoodsReceipt.receipt_number)).where(
            GoodsReceipt.receipt_number.like(f"{prefix}%")
        )
        result = self.db.execute(stmt).scalar()
        
        if result:
            last_num = int(result.split("-")[-1]) + 1
        else:
            last_num = 1
        
        return f"{prefix}{last_num:04d}"

    def create_goods_receipt(
        self,
        receipt_number: str,
        purchase_order_id: int,
        warehouse_id: int,
        received_date: datetime,
        received_by: int,
        quality_check_passed: Optional[bool],
        quality_notes: Optional[str],
        items: List[dict]
    ) -> GoodsReceipt:
        """Create goods receipt with items."""
        receipt = GoodsReceipt(
            receipt_number=receipt_number,
            purchase_order_id=purchase_order_id,
            warehouse_id=warehouse_id,
            received_date=received_date,
            received_by=received_by,
            quality_check_passed=quality_check_passed,
            quality_notes=quality_notes,
            created_at=datetime.now(),
        )
        
        self.db.add(receipt)
        self.db.flush()
        
        for item_data in items:
            item = GoodsReceiptItem(
                goods_receipt_id=receipt.id,
                po_item_id=item_data.get("po_item_id"),
                product_id=item_data.get("product_id"),
                product_name=item_data["product_name"],
                quantity_expected=item_data["quantity_expected"],
                quantity_received=item_data["quantity_received"],
                quantity_rejected=item_data.get("quantity_rejected", Decimal("0")),
                unit_of_measure=item_data.get("unit_of_measure", "unit"),
                batch_number=item_data.get("batch_number"),
                serial_numbers=item_data.get("serial_numbers"),
                created_at=datetime.now(),
            )
            self.db.add(item)
        
        self.db.flush()
        return receipt

    def get_goods_receipt_by_id(
        self,
        receipt_id: int,
        include_items: bool = False
    ) -> GoodsReceipt:
        """Get goods receipt by ID."""
        query = select(GoodsReceipt).where(
            GoodsReceipt.id == receipt_id,
            GoodsReceipt.deleted_at.is_(None)
        )
        
        if include_items:
            query = query.options(joinedload(GoodsReceipt.items))
        
        result = self.db.execute(query).scalar_one_or_none()
        
        if not result:
            raise GoodsReceiptNotFoundException(receipt_id)
        
        return result

    def update_receipt_status(
        self,
        receipt: GoodsReceipt,
        status: str
    ) -> None:
        """Update receipt status."""
        receipt.status = status
        receipt.updated_at = datetime.now()

    def soft_delete_receipt(self, receipt: GoodsReceipt) -> None:
        """Soft delete receipt."""
        receipt.deleted_at = datetime.now()
        receipt.updated_at = datetime.now()

    # ============== Comment Operations ==============

    def add_requisition_comment(
        self,
        requisition_id: int,
        author_id: int,
        content: str,
        is_internal: bool = True
    ) -> RequisitionComment:
        """Add comment to requisition."""
        comment = RequisitionComment(
            requisition_id=requisition_id,
            author_id=author_id,
            content=content,
            is_internal=is_internal,
            created_at=datetime.now(),
        )
        self.db.add(comment)
        self.db.flush()
        return comment

    def add_po_comment(
        self,
        po_id: int,
        author_id: int,
        content: str,
        is_internal: bool = True
    ) -> POComment:
        """Add comment to PO."""
        comment = POComment(
            purchase_order_id=po_id,
            author_id=author_id,
            content=content,
            is_internal=is_internal,
            created_at=datetime.now(),
        )
        self.db.add(comment)
        self.db.flush()
        return comment
