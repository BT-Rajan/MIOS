"""
FastAPI router for procurement module.

REST API endpoints for requisitions, purchase orders, and goods receipts.
No business logic - only HTTP handling.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.api.procurement.schemas import (
    PurchaseRequisitionCreate,
    PurchaseRequisitionUpdate,
    PurchaseRequisitionSubmit,
    PurchaseRequisitionApprove,
    PurchaseRequisitionReject,
    PurchaseRequisitionResponse,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderSubmit,
    PurchaseOrderApprove,
    PurchaseOrderSendToVendor,
    PurchaseOrderResponse,
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    CommentCreate,
    CommentResponse,
)
from backend.api.procurement.service import ProcurementService


router = APIRouter(prefix="/procurement", tags=["Procurement"])


def get_service(db: Session = Depends(get_db), current_user_id: int = 1):
    """Get procurement service instance."""
    # TODO: Get current_user_id from JWT token
    return ProcurementService(db=db, current_user_id=current_user_id)


# ============== Requisition Endpoints ==============

@router.post("/requisitions", response_model=dict)
async def create_requisition(
    data: PurchaseRequisitionCreate,
    service: ProcurementService = Depends(get_service)
):
    """Create new purchase requisition."""
    return service.create_requisition(data)


@router.get("/requisitions/{requisition_id}")
async def get_requisition(
    requisition_id: int = Path(..., description="Requisition ID"),
    service: ProcurementService = Depends(get_service)
):
    """Get requisition by ID."""
    return service.get_requisition(requisition_id)


@router.get("/requisitions")
async def list_requisitions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: ProcurementService = Depends(get_service)
):
    """List requisitions with pagination."""
    return service.list_requisitions(status=status, limit=limit, offset=offset)


@router.post("/requisitions/{requisition_id}/submit")
async def submit_requisition(
    requisition_id: int = Path(...),
    data: PurchaseRequisitionSubmit = None,
    service: ProcurementService = Depends(get_service)
):
    """Submit requisition for approval."""
    reason = data.reason if data else None
    return service.submit_requisition(requisition_id, reason)


@router.post("/requisitions/{requisition_id}/approve")
async def approve_requisition(
    requisition_id: int = Path(...),
    data: PurchaseRequisitionApprove = None,
    service: ProcurementService = Depends(get_service)
):
    """Approve requisition."""
    reason = data.reason if data else None
    return service.approve_requisition(requisition_id, reason)


@router.post("/requisitions/{requisition_id}/reject")
async def reject_requisition(
    requisition_id: int = Path(...),
    data: PurchaseRequisitionReject,
    service: ProcurementService = Depends(get_service)
):
    """Reject requisition."""
    return service.reject_requisition(requisition_id, data.reason)


@router.post("/requisitions/{requisition_id}/comments")
async def add_requisition_comment(
    requisition_id: int = Path(...),
    data: CommentCreate = None,
    service: ProcurementService = Depends(get_service)
):
    """Add comment to requisition."""
    return service.add_requisition_comment(
        requisition_id,
        data.content,
        data.is_internal
    )


# ============== Purchase Order Endpoints ==============

@router.post("/purchase-orders", response_model=dict)
async def create_purchase_order(
    data: PurchaseOrderCreate,
    service: ProcurementService = Depends(get_service)
):
    """Create new purchase order."""
    return service.create_purchase_order(data)


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(
    po_id: int = Path(..., description="PO ID"),
    service: ProcurementService = Depends(get_service)
):
    """Get purchase order by ID."""
    return service.get_purchase_order(po_id)


@router.get("/purchase-orders")
async def list_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: ProcurementService = Depends(get_service)
):
    """List purchase orders with pagination."""
    return service.list_purchase_orders(status=status, limit=limit, offset=offset)


@router.post("/purchase-orders/{po_id}/approve")
async def approve_purchase_order(
    po_id: int = Path(...),
    data: PurchaseOrderApprove = None,
    service: ProcurementService = Depends(get_service)
):
    """Approve purchase order."""
    reason = data.reason if data else None
    return service.approve_purchase_order(po_id, reason)


@router.post("/purchase-orders/{po_id}/send-to-vendor")
async def send_to_vendor(
    po_id: int = Path(...),
    data: PurchaseOrderSendToVendor = None,
    service: ProcurementService = Depends(get_service)
):
    """Mark PO as sent to vendor."""
    # TODO: Implement send_to_vendor in service
    return {"status": "sent_to_vendor"}


@router.post("/purchase-orders/{po_id}/comments")
async def add_po_comment(
    po_id: int = Path(...),
    data: CommentCreate = None,
    service: ProcurementService = Depends(get_service)
):
    """Add comment to purchase order."""
    return service.add_po_comment(po_id, data.content, data.is_internal)


# ============== Goods Receipt Endpoints ==============

@router.post("/goods-receipts", response_model=dict)
async def create_goods_receipt(
    data: GoodsReceiptCreate,
    service: ProcurementService = Depends(get_service)
):
    """Create goods receipt for PO delivery."""
    return service.create_goods_receipt(data)


@router.get("/goods-receipts/{receipt_id}")
async def get_goods_receipt(
    receipt_id: int = Path(..., description="Receipt ID"),
    service: ProcurementService = Depends(get_service)
):
    """Get goods receipt by ID."""
    return service.get_goods_receipt(receipt_id)


@router.get("/goods-receipts")
async def list_goods_receipts(
    po_id: Optional[int] = Query(None, description="Filter by PO ID"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: ProcurementService = Depends(get_service)
):
    """List goods receipts with pagination."""
    # TODO: Implement list_goods_receipts in service
    return {"items": [], "total": 0, "limit": limit, "offset": offset}
