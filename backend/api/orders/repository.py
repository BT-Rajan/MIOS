"""
Repository for Order module.

Centralized data access layer - no SQL in services.
All database operations go through this repository.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session, joinedload

from backend.api.orders.models import (
    Order,
    OrderItem,
    OrderComment,
    OrderStatus,
    OrderPriority,
)
from backend.api.orders.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderQueryParams,
)
from backend.api.orders.exceptions import OrderNotFoundException


class OrderRepository:
    """
    Repository for order data access.
    
    All CRUD operations for orders, items, and comments.
    No business logic - only data access.
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # ORDER CRUD OPERATIONS
    # =========================================================================

    def create_order(
        self,
        order_number: str,
        customer_id: int,
        created_by: int,
        order_date: datetime,
        priority: OrderPriority = OrderPriority.NORMAL,
        required_date: Optional[datetime] = None,
        shipping_address_id: Optional[int] = None,
        billing_address_id: Optional[int] = None,
        shipping_method: Optional[str] = None,
        shipping_cost: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        currency: str = "USD",
    ) -> Order:
        """Create a new order in DRAFT status."""
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            created_by=created_by,
            order_date=order_date,
            status=OrderStatus.DRAFT,
            priority=priority,
            required_date=required_date,
            shipping_address_id=shipping_address_id,
            billing_address_id=billing_address_id,
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            currency=currency,
            version=1,
        )
        self.db.add(order)
        self.db.flush()
        return order

    def get_order_by_id(self, order_id: int, include_items: bool = False) -> Optional[Order]:
        """Get order by ID with optional items."""
        query = select(Order).where(Order.id == order_id, Order.is_deleted == False)
        
        if include_items:
            query = query.options(joinedload(Order.items))
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        query = select(Order).where(
            Order.order_number == order_number,
            Order.is_deleted == False
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def order_exists(self, order_number: str) -> bool:
        """Check if order number already exists."""
        query = select(func.count()).where(
            Order.order_number == order_number,
            Order.is_deleted == False
        )
        result = self.db.execute(query)
        count = result.scalar()
        return count > 0

    def update_order(
        self,
        order: Order,
        data: OrderUpdate,
        updated_by: int,
        bump_version: bool = True,
    ) -> Order:
        """Update an existing order."""
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(order, field, value)
        
        if bump_version:
            order.version += 1
        
        order.updated_at = datetime.utcnow()
        self.db.flush()
        return order

    def update_order_status(
        self,
        order: Order,
        new_status: OrderStatus,
        user_id: Optional[int] = None,
        rejection_reason: Optional[str] = None,
    ) -> Order:
        """Update order status with audit fields."""
        order.status = new_status
        order.version += 1
        order.updated_at = datetime.utcnow()
        
        if new_status == OrderStatus.APPROVED and user_id:
            order.approved_by = user_id
        elif new_status == OrderStatus.REJECTED and user_id:
            order.rejected_by = user_id
            order.rejection_reason = rejection_reason
        
        self.db.flush()
        return order

    def soft_delete_order(self, order: Order, deleted_by: int) -> None:
        """Soft delete an order."""
        order.is_deleted = True
        order.deleted_at = datetime.utcnow()
        order.deleted_by = deleted_by
        order.version += 1
        self.db.flush()

    def list_orders(
        self,
        params: OrderQueryParams,
    ) -> Tuple[List[Order], int]:
        """
        List orders with filtering and pagination.
        
        Returns:
            Tuple of (orders list, total count)
        """
        # Build base query
        query = select(Order).where(Order.is_deleted == False)
        count_query = select(func.count()).where(Order.is_deleted == False)
        
        # Apply filters
        if params.status:
            query = query.where(Order.status == params.status)
            count_query = count_query.where(Order.status == params.status)
        
        if params.priority:
            query = query.where(Order.priority == params.priority)
            count_query = count_query.where(Order.priority == params.priority)
        
        if params.customer_id:
            query = query.where(Order.customer_id == params.customer_id)
            count_query = count_query.where(Order.customer_id == params.customer_id)
        
        if params.date_from:
            query = query.where(Order.order_date >= params.date_from)
            count_query = count_query.where(Order.order_date >= params.date_from)
        
        if params.date_to:
            query = query.where(Order.order_date <= params.date_to)
            count_query = count_query.where(Order.order_date <= params.date_to)
        
        # Get total count
        count_result = self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply ordering and pagination
        query = query.order_by(Order.order_date.desc())
        query = query.offset(params.offset).limit(params.limit)
        
        # Execute query
        result = self.db.execute(query)
        orders = result.scalars().all()
        
        return list(orders), total

    # =========================================================================
    # ORDER ITEM OPERATIONS
    # =========================================================================

    def create_order_item(
        self,
        order_id: int,
        product_id: int,
        product_code: str,
        product_name: str,
        quantity_ordered: int,
        unit_price: Decimal,
        discount_percent: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
    ) -> OrderItem:
        """Create a new order item."""
        line_total = (Decimal(quantity_ordered) * unit_price) * (
            Decimal("1") - (discount_percent / Decimal("100"))
        )
        
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            product_code=product_code,
            product_name=product_name,
            quantity_ordered=quantity_ordered,
            quantity_shipped=0,
            unit_price=unit_price,
            discount_percent=discount_percent,
            line_total=line_total,
            notes=notes,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get all items for an order."""
        query = select(OrderItem).where(OrderItem.order_id == order_id)
        query = query.order_by(OrderItem.id)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def update_order_item_quantity(
        self,
        item: OrderItem,
        quantity_ordered: int,
    ) -> OrderItem:
        """Update order item quantity and recalculate totals."""
        item.quantity_ordered = quantity_ordered
        item.line_total = (
            Decimal(quantity_ordered) * item.unit_price
        ) * (Decimal("1") - (item.discount_percent / Decimal("100")))
        self.db.flush()
        return item

    def delete_order_item(self, item: OrderItem) -> None:
        """Delete an order item (draft orders only)."""
        self.db.delete(item)
        self.db.flush()

    # =========================================================================
    # ORDER COMMENT OPERATIONS
    # =========================================================================

    def create_comment(
        self,
        order_id: int,
        user_id: int,
        comment: str,
        is_internal: bool = True,
    ) -> OrderComment:
        """Add a comment to an order."""
        order_comment = OrderComment(
            order_id=order_id,
            user_id=user_id,
            comment=comment,
            is_internal=is_internal,
        )
        self.db.add(order_comment)
        self.db.flush()
        return order_comment

    def get_order_comments(self, order_id: int) -> List[OrderComment]:
        """Get all comments for an order."""
        query = select(OrderComment).where(OrderComment.order_id == order_id)
        query = query.order_by(OrderComment.created_at.asc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def generate_order_number(self, prefix: str = "ORD") -> str:
        """Generate unique order number."""
        today = datetime.utcnow().strftime("%Y%m%d")
        query = select(func.max(Order.order_number)).where(
            Order.order_number.like(f"{prefix}-{today}-%"),
            Order.is_deleted == False,
        )
        result = self.db.execute(query)
        max_number = result.scalar()
        
        if max_number:
            last_seq = int(max_number.split("-")[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}-{today}-{new_seq:05d}"
