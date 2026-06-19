"""
Service layer for Order module - Core operations.

Handles order creation, retrieval, and basic operations.
Workflow operations are in service_workflow.py.
All business logic resides here - no logic in routers or frontend.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.api.orders.repository import OrderRepository
from backend.api.orders.models import OrderStatus, OrderPriority
from backend.api.orders.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderQueryParams,
    OrderDetailResponse,
    OrderSummary,
)
from backend.api.orders.exceptions import (
    OrderNotFoundException,
    OrderDuplicateNumberError,
)
from backend.api.orders.validators import OrderValidators
from backend.shared.audit import AuditEngine
from backend.shared.events import EventBus
from backend.shared.permissions import PermissionEngine


class OrderService:
    """
    Order business logic service for core operations.
    
    All order operations go through this service.
    Coordinates with inventory, customers, and other services.
    """

    def __init__(
        self,
        db: Session,
        audit_engine: AuditEngine,
        event_bus: EventBus,
        permission_engine: PermissionEngine,
        inventory_service=None,
    ):
        self.db = db
        self.repository = OrderRepository(db)
        self.audit = audit_engine
        self.event_bus = event_bus
        self.permissions = permission_engine
        self.inventory_service = inventory_service

    def create_order(
        self,
        data: OrderCreate,
        user_id: int,
    ) -> OrderDetailResponse:
        """
        Create a new order in DRAFT status.
        
        Business rules:
        - Validates all input data
        - Checks customer exists
        - Generates unique order number
        - Creates audit trail
        """
        # Validate input
        OrderValidators.validate_order_create(data)
        
        # Check permissions
        self.permissions.check_permission(user_id, "order:create")
        
        # Generate unique order number
        order_number = self.repository.generate_order_number()
        
        if self.repository.order_exists(order_number):
            raise OrderDuplicateNumberError(order_number)
        
        # Create order header
        order = self.repository.create_order(
            order_number=order_number,
            customer_id=data.customer_id,
            created_by=user_id,
            order_date=datetime.utcnow(),
            priority=OrderPriority(data.priority.value),
            required_date=data.required_date,
            shipping_address_id=data.shipping_address_id,
            billing_address_id=data.billing_address_id,
            shipping_method=data.shipping_method,
            shipping_cost=data.shipping_cost,
            tax_amount=data.tax_amount,
            discount_amount=data.discount_amount,
            currency=data.currency,
        )
        
        # Create order items
        for item_data in data.items:
            product = self.inventory_service.get_product_by_id(item_data.product_id)
            
            self.repository.create_order_item(
                order_id=order.id,
                product_id=item_data.product_id,
                product_code=product.code,
                product_name=product.name,
                quantity_ordered=item_data.quantity_ordered,
                unit_price=item_data.unit_price,
                discount_percent=item_data.discount_percent,
                notes=item_data.notes,
            )
        
        # Recalculate totals
        order.calculate_totals()
        self.db.flush()
        
        # Audit trail
        self.audit.record_event(
            entity="order",
            entity_id=order.id,
            action="created",
            old_state=None,
            new_state=OrderStatus.DRAFT.value,
            actor_id=user_id,
            reason="New order created",
        )
        
        # Publish event
        self.event_bus.publish("order_created", {"order_id": order.id})
        
        return self.get_order_detail(order.id)

    def get_order_detail(self, order_id: int) -> OrderDetailResponse:
        """Get complete order details with items."""
        order = self.repository.get_order_by_id(order_id, include_items=True)
        
        if not order:
            raise OrderNotFoundException(order_id)
        
        return OrderDetailResponse.model_validate(order)

    def list_orders(
        self,
        params: OrderQueryParams,
        user_id: int,
    ) -> Tuple[List[OrderSummary], int]:
        """List orders with filtering and pagination."""
        self.permissions.check_permission(user_id, "order:read")
        
        orders, total = self.repository.list_orders(params)
        
        summaries = []
        for order in orders:
            summaries.append(OrderSummary(
                order_number=order.order_number,
                customer_name=order.customer.name if order.customer else "Unknown",
                status=order.status,
                priority=order.priority,
                total_amount=order.total_amount,
                order_date=order.order_date,
                required_date=order.required_date,
                is_late=self._is_order_late(order),
            ))
        
        return summaries, total

    def add_comment(
        self,
        order_id: int,
        comment: str,
        is_internal: bool,
        user_id: int,
    ) -> dict:
        """Add a comment to an order."""
        order = self.repository.get_order_by_id(order_id)
        
        if not order:
            raise OrderNotFoundException(order_id)
        
        self.permissions.check_permission(user_id, "order:comment")
        
        comment_obj = self.repository.create_comment(
            order_id=order_id,
            user_id=user_id,
            comment=comment,
            is_internal=is_internal,
        )
        
        # Audit
        self.audit.record_event(
            entity="order_comment",
            entity_id=comment_obj.id,
            action="created",
            old_state=None,
            new_state="active",
            actor_id=user_id,
            reason="Comment added",
        )
        
        return {"id": comment_obj.id, "created_at": comment_obj.created_at}

    def _is_order_late(self, order) -> bool:
        """Check if order is past required date."""
        if not order.required_date:
            return False
        return datetime.utcnow() > order.required_date and order.status not in [
            OrderStatus.SHIPPED,
            OrderStatus.COMPLETED,
        ]
