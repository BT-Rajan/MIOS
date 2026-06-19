"""
Service layer for procurement module.

Business logic for requisitions, purchase orders, and goods receipts.
Uses repository pattern and shared engines.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.api.procurement.repository import ProcurementRepository
from backend.api.procurement.models import RequisitionStatus, PurchaseOrderStatus
from backend.api.procurement.schemas import (
    PurchaseRequisitionCreate,
    PurchaseOrderCreate,
    GoodsReceiptCreate,
)
from backend.api.procurement.validators import ProcurementValidators
from backend.api.procurement.exceptions import (
    RequisitionInvalidStatusTransition,
    PurchaseOrderInvalidStatusTransition,
    RequisitionAlreadyConverted,
    PurchaseOrderFinancialDataImmutable,
)
from backend.shared.audit.engine import AuditEngine
from backend.shared.events.engine import EventBus
from backend.shared.permissions.engine import PermissionEngine


class ProcurementService:
    """
    Business logic for procurement operations.
    
    All state changes create audit records.
    All operations use repository layer.
    """

    def __init__(self, db: Session, current_user_id: int):
        self.db = db
        self.current_user_id = current_user_id
        self.repo = ProcurementRepository(db)
        self.audit = AuditEngine(db)
        self.event_bus = EventBus()
        self.permissions = PermissionEngine()

    # ============== Requisition Operations ==============

    def create_requisition(self, data: PurchaseRequisitionCreate) -> dict:
        """
        Create new purchase requisition.
        
        Args:
            data: Requisition creation data
            
        Returns:
            Created requisition data
        """
        # Validate
        ProcurementValidators.validate_items_not_empty(data.items)
        if data.priority:
            ProcurementValidators.validate_priority(data.priority)
        
        # Generate number
        requisition_number = self.repo.generate_requisition_number()
        
        # Prepare items
        items_data = []
        for item in data.items:
            items_data.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_code": getattr(item, 'product_code', None),
                "quantity_requested": item.quantity_requested,
                "unit_of_measure": getattr(item, 'unit_of_measure', 'unit'),
                "estimated_unit_price": item.estimated_unit_price,
                "justification": item.justification,
            })
        
        # Create
        requisition = self.repo.create_requisition(
            requisition_number=requisition_number,
            requester_id=self.current_user_id,
            department_id=data.department_id,
            suggested_vendor_id=data.suggested_vendor_id,
            priority=data.priority,
            required_by_date=data.required_by_date,
            notes=data.notes,
            items=items_data,
        )
        
        # Audit
        self.audit.record_event(
            entity="purchase_requisition",
            entity_id=requisition.id,
            action="created",
            actor_id=self.current_user_id,
            new_state={"status": "draft", "number": requisition_number},
            reason="New requisition created"
        )
        
        # Event
        self.event_bus.publish("requisition_created", {
            "requisition_id": requisition.id,
            "requisition_number": requisition_number,
        })
        
        return {
            "id": requisition.id,
            "requisition_number": requisition.requisition_number,
            "status": requisition.status.value,
        }

    def get_requisition(self, requisition_id: int) -> dict:
        """Get requisition by ID."""
        requisition = self.repo.get_requisition_by_id(
            requisition_id, 
            include_items=True
        )
        
        return {
            "id": requisition.id,
            "requisition_number": requisition.requisition_number,
            "requester_id": requisition.requester_id,
            "status": requisition.status.value,
            "estimated_total": requisition.estimated_total,
            "currency": requisition.currency,
            "priority": requisition.priority,
            "required_by_date": requisition.required_by_date,
            "notes": requisition.notes,
            "submitted_at": requisition.submitted_at,
            "approved_at": requisition.approved_at,
            "rejection_reason": requisition.rejection_reason,
            "created_at": requisition.created_at,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity_requested": item.quantity_requested,
                    "estimated_unit_price": item.estimated_unit_price,
                    "estimated_line_total": item.estimated_line_total,
                }
                for item in requisition.items
            ]
        }

    def submit_requisition(self, requisition_id: int, reason: Optional[str] = None) -> dict:
        """Submit requisition for approval."""
        requisition = self.repo.get_requisition_by_id(requisition_id)
        
        # Validate transition
        if requisition.status != RequisitionStatus.DRAFT:
            raise RequisitionInvalidStatusTransition(
                requisition.status.value, 
                "submitted"
            )
        
        # Update status
        old_status = requisition.status.value
        self.repo.update_requisition_status(
            requisition, 
            RequisitionStatus.SUBMITTED
        )
        
        # Audit
        self.audit.record_event(
            entity="purchase_requisition",
            entity_id=requisition.id,
            action="submitted",
            actor_id=self.current_user_id,
            old_state={"status": old_status},
            new_state={"status": "submitted"},
            reason=reason or "Submitted for approval"
        )
        
        # Event
        self.event_bus.publish("requisition_submitted", {
            "requisition_id": requisition.id,
        })
        
        return {"status": "submitted"}

    def approve_requisition(
        self, 
        requisition_id: int, 
        reason: Optional[str] = None
    ) -> dict:
        """Approve requisition."""
        requisition = self.repo.get_requisition_by_id(requisition_id)
        
        # Check permission
        if not self.permissions.can(
            user_id=self.current_user_id,
            action="approve_requisition",
            entity="purchase_requisition",
            entity_id=requisition.id
        ):
            raise PermissionError("User cannot approve requisitions")
        
        # Validate transition
        if requisition.status != RequisitionStatus.SUBMITTED:
            raise RequisitionInvalidStatusTransition(
                requisition.status.value,
                "approved"
            )
        
        # Update status
        old_status = requisition.status.value
        self.repo.update_requisition_status(
            requisition,
            RequisitionStatus.APPROVED,
            approved_by=self.current_user_id
        )
        
        # Audit
        self.audit.record_event(
            entity="purchase_requisition",
            entity_id=requisition.id,
            action="approved",
            actor_id=self.current_user_id,
            old_state={"status": old_status},
            new_state={"status": "approved"},
            reason=reason or "Approved"
        )
        
        # Event
        self.event_bus.publish("requisition_approved", {
            "requisition_id": requisition.id,
        })
        
        return {"status": "approved"}

    def reject_requisition(
        self,
        requisition_id: int,
        reason: str
    ) -> dict:
        """Reject requisition."""
        ProcurementValidators.validate_rejection_reason(reason)
        
        requisition = self.repo.get_requisition_by_id(requisition_id)
        
        # Validate transition
        if requisition.status != RequisitionStatus.SUBMITTED:
            raise RequisitionInvalidStatusTransition(
                requisition.status.value,
                "rejected"
            )
        
        # Update status
        old_status = requisition.status.value
        self.repo.update_requisition_status(
            requisition,
            RequisitionStatus.REJECTED,
            approved_by=self.current_user_id
        )
        self.repo.set_requisition_rejection_reason(requisition, reason)
        
        # Audit
        self.audit.record_event(
            entity="purchase_requisition",
            entity_id=requisition.id,
            action="rejected",
            actor_id=self.current_user_id,
            old_state={"status": old_status},
            new_state={"status": "rejected", "reason": reason},
            reason=reason
        )
        
        # Event
        self.event_bus.publish("requisition_rejected", {
            "requisition_id": requisition.id,
            "reason": reason,
        })
        
        return {"status": "rejected"}

    def list_requisitions(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """List requisitions with pagination."""
        status_enum = None
        if status:
            status_enum = RequisitionStatus(status)
        
        requisitions, total = self.repo.list_requisitions(
            status=status_enum,
            requester_id=None,
            limit=limit,
            offset=offset
        )
        
        return {
            "items": [
                {
                    "id": r.id,
                    "requisition_number": r.requisition_number,
                    "status": r.status.value,
                    "estimated_total": r.estimated_total,
                    "created_at": r.created_at,
                }
                for r in requisitions
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    # ============== Purchase Order Operations ==============

    def create_purchase_order(self, data: PurchaseOrderCreate) -> dict:
        """Create new purchase order."""
        # Validate
        ProcurementValidators.validate_items_not_empty(data.items)
        
        # Check if requisition exists and is approved
        if data.requisition_id:
            requisition = self.repo.get_requisition_by_id(data.requisition_id)
            if requisition.status != RequisitionStatus.APPROVED:
                raise ValueError("Only approved requisitions can be converted to PO")
            
            # Check if already converted
            if requisition.purchase_order:
                raise RequisitionAlreadyConverted(
                    requisition.id,
                    requisition.purchase_order.po_number
                )
        
        # Generate number
        po_number = self.repo.generate_po_number()
        
        # Prepare items
        items_data = []
        subtotal = Decimal("0.00")
        
        for item in data.items:
            line_total = item.unit_price * item.quantity_ordered
            subtotal += line_total
            
            items_data.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_code": getattr(item, 'product_code', None),
                "quantity_ordered": item.quantity_ordered,
                "unit_of_measure": getattr(item, 'unit_of_measure', 'unit'),
                "unit_price": item.unit_price,
                "line_total": line_total,
                "expected_delivery_date": item.expected_delivery_date,
            })
        
        # Create
        po = self.repo.create_purchase_order(
            po_number=po_number,
            requisition_id=data.requisition_id,
            vendor_id=data.vendor_id,
            order_date=datetime.now(),
            expected_delivery_date=data.expected_delivery_date,
            shipping_method=data.shipping_method,
            ship_to_address_id=data.ship_to_address_id,
            notes=data.notes,
            internal_notes=data.internal_notes,
            items=items_data,
        )
        
        # Update requisition if linked
        if data.requisition_id:
            self.repo.update_requisition_status(
                requisition,
                RequisitionStatus.CONVERTED
            )
        
        # Audit
        self.audit.record_event(
            entity="purchase_order",
            entity_id=po.id,
            action="created",
            actor_id=self.current_user_id,
            new_state={"status": "draft", "number": po_number},
            reason="New PO created"
        )
        
        # Event
        self.event_bus.publish("purchase_order_created", {
            "po_id": po.id,
            "po_number": po_number,
        })
        
        return {
            "id": po.id,
            "po_number": po.po_number,
            "status": po.status.value,
        }

    def get_purchase_order(self, po_id: int) -> dict:
        """Get PO by ID."""
        po = self.repo.get_purchase_order_by_id(po_id, include_items=True)
        
        return {
            "id": po.id,
            "po_number": po.po_number,
            "vendor_id": po.vendor_id,
            "status": po.status.value,
            "order_date": po.order_date,
            "expected_delivery_date": po.expected_delivery_date,
            "subtotal": po.subtotal,
            "tax_amount": po.tax_amount,
            "shipping_cost": po.shipping_cost,
            "total_amount": po.total_amount,
            "currency": po.currency,
            "notes": po.notes,
            "created_at": po.created_at,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity_ordered": item.quantity_ordered,
                    "quantity_received": item.quantity_received,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total,
                }
                for item in po.items
            ]
        }

    def approve_purchase_order(
        self,
        po_id: int,
        reason: Optional[str] = None
    ) -> dict:
        """Approve purchase order."""
        po = self.repo.get_purchase_order_by_id(po_id)
        
        # Check permission
        if not self.permissions.can(
            user_id=self.current_user_id,
            action="approve_purchase_order",
            entity="purchase_order",
            entity_id=po.id
        ):
            raise PermissionError("User cannot approve purchase orders")
        
        # Validate transition
        if po.status != PurchaseOrderStatus.SUBMITTED:
            raise PurchaseOrderInvalidStatusTransition(
                po.status.value,
                "approved"
            )
        
        # Update status
        old_status = po.status.value
        self.repo.update_po_status(
            po,
            PurchaseOrderStatus.APPROVED,
            approved_by=self.current_user_id
        )
        
        # Audit
        self.audit.record_event(
            entity="purchase_order",
            entity_id=po.id,
            action="approved",
            actor_id=self.current_user_id,
            old_state={"status": old_status},
            new_state={"status": "approved"},
            reason=reason or "Approved"
        )
        
        # Event
        self.event_bus.publish("purchase_order_approved", {
            "po_id": po.id,
        })
        
        return {"status": "approved"}

    def list_purchase_orders(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """List POs with pagination."""
        status_enum = None
        if status:
            status_enum = PurchaseOrderStatus(status)
        
        orders, total = self.repo.list_purchase_orders(
            status=status_enum,
            limit=limit,
            offset=offset
        )
        
        return {
            "items": [
                {
                    "id": o.id,
                    "po_number": o.po_number,
                    "vendor_id": o.vendor_id,
                    "status": o.status.value,
                    "total_amount": o.total_amount,
                    "created_at": o.created_at,
                }
                for o in orders
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    # ============== Goods Receipt Operations ==============

    def create_goods_receipt(self, data: GoodsReceiptCreate) -> dict:
        """Create goods receipt from PO delivery."""
        # Validate items
        ProcurementValidators.validate_items_not_empty(data.items)
        
        # Generate number
        receipt_number = self.repo.generate_receipt_number()
        
        # Prepare items
        items_data = []
        for item in data.items:
            ProcurementValidators.validate_received_quantity(
                item.quantity_received,
                item.quantity_expected
            )
            
            items_data.append({
                "po_item_id": item.po_item_id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity_expected": item.quantity_expected,
                "quantity_received": item.quantity_received,
                "quantity_rejected": item.quantity_rejected,
                "unit_of_measure": getattr(item, 'unit_of_measure', 'unit'),
                "batch_number": item.batch_number,
                "serial_numbers": item.serial_numbers,
            })
        
        # Create receipt
        receipt = self.repo.create_goods_receipt(
            receipt_number=receipt_number,
            purchase_order_id=data.purchase_order_id,
            warehouse_id=data.warehouse_id,
            received_date=data.received_date,
            received_by=self.current_user_id,
            quality_check_passed=data.quality_check_passed,
            quality_notes=data.quality_notes,
            items=items_data,
        )
        
        # Update PO status if fully received
        po = self.repo.get_purchase_order_by_id(data.purchase_order_id)
        all_received = all(
            item.quantity_received >= item.quantity_ordered
            for item in po.items
        )
        if all_received and po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED:
            self.repo.update_po_status(po, PurchaseOrderStatus.COMPLETED)
        elif any(
            item.quantity_received > 0 for item in po.items
        ) and po.status == PurchaseOrderStatus.SENT_TO_VENDOR:
            self.repo.update_po_status(po, PurchaseOrderStatus.PARTIALLY_RECEIVED)
        
        # Audit
        self.audit.record_event(
            entity="goods_receipt",
            entity_id=receipt.id,
            action="created",
            actor_id=self.current_user_id,
            new_state={"status": "received", "number": receipt_number},
            reason="Goods received"
        )
        
        # Event - triggers inventory update
        self.event_bus.publish("goods_received", {
            "receipt_id": receipt.id,
            "po_id": data.purchase_order_id,
            "warehouse_id": data.warehouse_id,
            "items": items_data,
        })
        
        return {
            "id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "status": receipt.status,
        }

    def get_goods_receipt(self, receipt_id: int) -> dict:
        """Get goods receipt by ID."""
        receipt = self.repo.get_goods_receipt_by_id(receipt_id, include_items=True)
        
        return {
            "id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "purchase_order_id": receipt.purchase_order_id,
            "received_date": receipt.received_date,
            "warehouse_id": receipt.warehouse_id,
            "received_by": receipt.received_by,
            "status": receipt.status,
            "quality_check_passed": receipt.quality_check_passed,
            "quality_notes": receipt.quality_notes,
            "created_at": receipt.created_at,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity_expected": item.quantity_expected,
                    "quantity_received": item.quantity_received,
                    "quantity_rejected": item.quantity_rejected,
                    "batch_number": item.batch_number,
                }
                for item in receipt.items
            ]
        }

    # ============== Comment Operations ==============

    def add_requisition_comment(
        self,
        requisition_id: int,
        content: str,
        is_internal: bool = True
    ) -> dict:
        """Add comment to requisition."""
        comment = self.repo.add_requisition_comment(
            requisition_id=requisition_id,
            author_id=self.current_user_id,
            content=content,
            is_internal=is_internal,
        )
        
        self.audit.record_event(
            entity="requisition_comment",
            entity_id=comment.id,
            action="created",
            actor_id=self.current_user_id,
            new_state={"content": content[:100]},
            reason="Comment added"
        )
        
        return {"id": comment.id}

    def add_po_comment(
        self,
        po_id: int,
        content: str,
        is_internal: bool = True
    ) -> dict:
        """Add comment to PO."""
        comment = self.repo.add_po_comment(
            po_id=po_id,
            author_id=self.current_user_id,
            content=content,
            is_internal=is_internal,
        )
        
        self.audit.record_event(
            entity="po_comment",
            entity_id=comment.id,
            action="created",
            actor_id=self.current_user_id,
            new_state={"content": content[:100]},
            reason="Comment added"
        )
        
        return {"id": comment.id}
