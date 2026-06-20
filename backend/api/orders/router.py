"""
FastAPI router for Order module.

Exposes REST API endpoints for order management.
No business logic - all operations delegated to services.
Follows enterprise patterns for consistency.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.shared.audit import AuditEngine
from backend.shared.workflow import WorkflowEngine
from backend.shared.events import EventBus
from backend.shared.permissions import PermissionEngine

from backend.api.orders.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderSubmit,
    OrderApprove,
    OrderReject,
    OrderCancel,
    OrderQueryParams,
    OrderDetailResponse,
    OrderSummary,
    OrderCommentCreate,
    OrderCommentResponse,
)
from backend.api.orders.service import OrderService
from backend.api.orders.service_workflow import OrderWorkflowService
from backend.api.orders.exceptions import (
    OrderException,
    OrderNotFoundException,
    OrderInvalidStatusTransitionError,
    OrderDuplicateNumberError,
)


router = APIRouter(prefix="/orders", tags=["orders"])


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_order_service(db: : Session):
    """Get order service with all dependencies."""
    return OrderService(
        db=db,
        audit_engine=AuditEngine(db),
        event_bus=EventBus(),
        permission_engine=PermissionEngine(db),
        inventory_service=None,  # Inject when available
    )


def get_order_workflow_service(db: : Session):
    """Get order workflow service with all dependencies."""
    from backend.api.orders.repository import OrderRepository
    
    return OrderWorkflowService(
        db=db,
        repository=OrderRepository(db),
        audit_engine=AuditEngine(db),
        workflow_engine=WorkflowEngine(),
        event_bus=EventBus(),
        permission_engine=PermissionEngine(db),
        inventory_service=None,  # Inject when available
    )


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================


@router.exception_handler(OrderNotFoundException)
async def order_not_found_handler(request, exc: OrderNotFoundException):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.exception_handler(OrderInvalidStatusTransitionError)
async def invalid_transition_handler(request, exc: OrderInvalidStatusTransitionError):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.exception_handler(OrderDuplicateNumberError)
async def duplicate_number_handler(request, exc: OrderDuplicateNumberError):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.exception_handler(OrderException)
async def order_exception_handler(request, exc: OrderException):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# =============================================================================
# ORDER ENDPOINTS
# =============================================================================


@router.post("", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """Create a new order in DRAFT status."""
    return service.create_order(data=data, user_id=current_user["id"])


@router.get("", response_model=List[OrderSummary])
def list_orders(
    status_filter: str = Query(None, alias="status"),
    priority: str = Query(None),
    customer_id: int = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """List orders with filtering and pagination."""
    params = OrderQueryParams(
        status=status_filter,
        priority=priority,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )
    orders, total = service.list_orders(params=params, user_id=current_user["id"])
    return orders


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """Get complete order details with items."""
    return service.get_order_detail(order_id=order_id)


@router.post("/{order_id}/submit", response_model=OrderDetailResponse)
def submit_order(
    order_id: int,
    data: OrderSubmit,
    current_user: dict = Depends(get_current_user),
    workflow_service: OrderWorkflowService = Depends(get_order_workflow_service),
):
    """Submit a draft order for approval."""
    return workflow_service.submit_order(
        order_id=order_id, data=data, user_id=current_user["id"]
    )


@router.post("/{order_id}/approve", response_model=OrderDetailResponse)
def approve_order(
    order_id: int,
    data: OrderApprove,
    current_user: dict = Depends(get_current_user),
    workflow_service: OrderWorkflowService = Depends(get_order_workflow_service),
):
    """Approve a submitted order."""
    return workflow_service.approve_order(
        order_id=order_id, data=data, user_id=current_user["id"]
    )


@router.post("/{order_id}/reject", response_model=OrderDetailResponse)
def reject_order(
    order_id: int,
    data: OrderReject,
    current_user: dict = Depends(get_current_user),
    workflow_service: OrderWorkflowService = Depends(get_order_workflow_service),
):
    """Reject a submitted order."""
    return workflow_service.reject_order(
        order_id=order_id, data=data, user_id=current_user["id"]
    )


@router.post("/{order_id}/cancel", response_model=OrderDetailResponse)
def cancel_order(
    order_id: int,
    data: OrderCancel,
    current_user: dict = Depends(get_current_user),
    workflow_service: OrderWorkflowService = Depends(get_order_workflow_service),
):
    """Cancel an order (draft or approved only)."""
    return workflow_service.cancel_order(
        order_id=order_id, data=data, user_id=current_user["id"]
    )


# =============================================================================
# COMMENT ENDPOINTS
# =============================================================================


@router.post("/{order_id}/comments", response_model=OrderCommentResponse)
def add_comment(
    order_id: int,
    data: OrderCommentCreate,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """Add a comment to an order."""
    result = service.add_comment(
        order_id=order_id,
        comment=data.comment,
        is_internal=data.is_internal,
        user_id=current_user["id"],
    )
    return OrderCommentResponse(**result, order_id=order_id, user_id=current_user["id"])
