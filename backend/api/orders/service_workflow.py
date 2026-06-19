"""
Service layer for Order module - Workflow operations.

Handles order workflow state transitions: submit, approve, reject, cancel.
All business logic resides here - no logic in routers or frontend.
Kept separate from core service to maintain file size under 500 lines.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.api.orders.repository import OrderRepository
from backend.api.orders.models import OrderStatus
from backend.api.orders.schemas import (
    OrderSubmit,
    OrderApprove,
    OrderReject,
    OrderCancel,
    OrderDetailResponse,
)
from backend.api.orders.exceptions import (
    OrderNotFoundException,
    OrderInvalidStatusTransitionError,
)
from backend.api.orders.validators import OrderValidators
from backend.shared.audit import AuditEngine
from backend.shared.workflow import WorkflowEngine
from backend.shared.events import EventBus
from backend.shared.permissions import PermissionEngine


class OrderWorkflowService:
    """
    Order workflow business logic service.
    
    Handles all state transitions with proper validation,
    audit trails, and event publishing.
    """

    VALID_TRANSITIONS = {
        OrderStatus.DRAFT: [OrderStatus.SUBMITTED, OrderStatus.CANCELLED],
        OrderStatus.SUBMITTED: [OrderStatus.APPROVED, OrderStatus.REJECTED],
        OrderStatus.APPROVED: [OrderStatus.SCHEDULED, OrderStatus.CANCELLED],
        OrderStatus.REJECTED: [],
        OrderStatus.SCHEDULED: [OrderStatus.IN_PRODUCTION],
        OrderStatus.IN_PRODUCTION: [OrderStatus.COMPLETED],
        OrderStatus.COMPLETED: [OrderStatus.SHIPPED],
        OrderStatus.SHIPPED: [],
        OrderStatus.CANCELLED: [],
    }

    def __init__(
        self,
        db: Session,
        repository: OrderRepository,
        audit_engine: AuditEngine,
        workflow_engine: WorkflowEngine,
        event_bus: EventBus,
        permission_engine: PermissionEngine,
        inventory_service=None,
    ):
        self.db = db
        self.repository = repository
        self.audit = audit_engine
        self.workflow = workflow_engine
        self.event_bus = event_bus
        self.permissions = permission_engine
        self.inventory_service = inventory_service

    def _validate_transition(self, order, new_status: OrderStatus) -> None:
        """Validate status transition is allowed."""
        allowed = self.VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise OrderInvalidStatusTransitionError(
                order.status.value, new_status.value
            )

    def _transition_and_audit(
        self,
        order,
        new_status: OrderStatus,
        action: str,
        user_id: int,
        reason: str,
        extra_fields: Optional[dict] = None,
    ) -> None:
        """Perform workflow transition with audit trail."""
        old_status = order.status
        
        # Transition workflow
        self.workflow.transition(
            entity="order",
            entity_id=order.id,
            from_state=old_status.value,
            to_state=new_status.value,
            allowed_transitions=self.VALID_TRANSITIONS[order.status],
        )
        
        # Update status
        update_kwargs = extra_fields or {}
        if "user_id" not in update_kwargs:
            update_kwargs["user_id"] = user_id
        self.repository.update_order_status(order, new_status, **update_kwargs)
        
        # Audit
        self.audit.record_event(
            entity="order",
            entity_id=order.id,
            action=action,
            old_state=old_status.value,
            new_state=new_status.value,
            actor_id=user_id,
            reason=reason,
        )

    def submit_order(
        self,
        order_id: int,
        data: OrderSubmit,
        user_id: int,
    ) -> OrderDetailResponse:
        """Submit a draft order for approval."""
        order = self.repository.get_order_by_id(order_id, include_items=True)
        
        if not order:
            raise OrderNotFoundException(order_id)
        
        if order.status != OrderStatus.DRAFT:
            raise OrderInvalidStatusTransitionError(
                order.status.value, OrderStatus.SUBMITTED.value
            )
        
        self.permissions.check_permission(user_id, "order:submit")
        
        # Transition and audit
        self._transition_and_audit(
            order=order,
            new_status=OrderStatus.SUBMITTED,
            action="submitted",
            user_id=user_id,
            reason=data.reason or "Order submitted for approval",
        )
        
        # Publish event
        self.event_bus.publish("order_submitted", {"order_id": order_id})
        
        return OrderDetailResponse.model_validate(order)

    def approve_order(
        self,
        order_id: int,
        data: OrderApprove,
        user_id: int,
    ) -> OrderDetailResponse:
        """Approve a submitted order and reserve inventory."""
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise OrderNotFoundException(order_id)
        
        self._validate_transition(order, OrderStatus.APPROVED)
        self.permissions.check_permission(user_id, "order:approve")
        
        # Transition and audit
        self._transition_and_audit(
            order=order,
            new_status=OrderStatus.APPROVED,
            action="approved",
            user_id=user_id,
            reason=data.reason or "Order approved",
            extra_fields={"user_id": user_id},
        )
        
        # Reserve inventory
        if self.inventory_service:
            items = self.repository.get_order_items(order_id)
            for item in items:
                self.inventory_service.reserve_stock(
                    product_id=item.product_id,
                    quantity=item.quantity_ordered,
                    reference_type="order",
                    reference_id=order_id,
                )
        
        # Publish event
        self.event_bus.publish("order_approved", {"order_id": order_id})
        
        return OrderDetailResponse.model_validate(order)

    def reject_order(
        self,
        order_id: int,
        data: OrderReject,
        user_id: int,
    ) -> OrderDetailResponse:
        """Reject a submitted order."""
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise OrderNotFoundException(order_id)
        
        self._validate_transition(order, OrderStatus.REJECTED)
        self.permissions.check_permission(user_id, "order:reject")
        OrderValidators.validate_reason(data.reason, required=True)
        
        # Transition and audit
        old_status = order.status
        self.workflow.transition(
            entity="order",
            entity_id=order_id,
            from_state=old_status.value,
            to_state=OrderStatus.REJECTED.value,
            allowed_transitions=self.VALID_TRANSITIONS[order.status],
        )
        
        self.repository.update_order_status(
            order, OrderStatus.REJECTED, user_id=user_id, rejection_reason=data.reason
        )
        
        # Audit
        self.audit.record_event(
            entity="order",
            entity_id=order_id,
            action="rejected",
            old_state=old_status.value,
            new_state=OrderStatus.REJECTED.value,
            actor_id=user_id,
            reason=data.reason,
        )
        
        # Publish event
        self.event_bus.publish("order_rejected", {"order_id": order_id})
        
        return OrderDetailResponse.model_validate(order)

    def cancel_order(
        self,
        order_id: int,
        data: OrderCancel,
        user_id: int,
    ) -> OrderDetailResponse:
        """Cancel an order (draft or approved only)."""
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise OrderNotFoundException(order_id)
        
        self._validate_transition(order, OrderStatus.CANCELLED)
        self.permissions.check_permission(user_id, "order:cancel")
        OrderValidators.validate_reason(data.reason, required=True)
        
        # Release inventory if approved
        if order.status == OrderStatus.APPROVED and self.inventory_service:
            items = self.repository.get_order_items(order_id)
            for item in items:
                self.inventory_service.release_reservation(
                    product_id=item.product_id,
                    quantity=item.quantity_ordered,
                    reference_type="order",
                    reference_id=order_id,
                )
        
        # Transition and audit
        self._transition_and_audit(
            order=order,
            new_status=OrderStatus.CANCELLED,
            action="cancelled",
            user_id=user_id,
            reason=data.reason,
        )
        
        # Publish event
        self.event_bus.publish("order_cancelled", {"order_id": order_id})
        
        return OrderDetailResponse.model_validate(order)
