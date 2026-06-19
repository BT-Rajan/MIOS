"""
Validators for Order module.

Reusable validation functions using shared ValidationEngine.
No duplicated logic - all validators are centralized here.
"""

from decimal import Decimal
from typing import List, Optional

from backend.shared.validation import ValidationEngine
from backend.api.orders.schemas import OrderCreate, OrderItemCreate
from backend.api.orders.exceptions import (
    OrderInvalidItemError,
    OrderInsufficientInventoryError,
)


class OrderValidators:
    """
    Centralized order validators.
    
    All validation logic is reusable and called by services.
    No validation logic in routers or frontend.
    """

    @staticmethod
    def validate_order_create(data: OrderCreate) -> None:
        """
        Validate order creation request.
        
        Args:
            data: Order creation schema
            
        Raises:
            OrderInvalidItemError: If any item is invalid
        """
        # Validate currency code
        ValidationEngine.validate_currency_code(data.currency)
        
        # Validate shipping cost
        if data.shipping_cost < 0:
            raise OrderInvalidItemError("Shipping cost cannot be negative")
        
        # Validate tax amount
        if data.tax_amount < 0:
            raise OrderInvalidItemError("Tax amount cannot be negative")
        
        # Validate discount amount
        if data.discount_amount < 0:
            raise OrderInvalidItemError("Discount amount cannot be negative")
        
        # Validate each order item
        for idx, item in enumerate(data.items):
            OrderValidators.validate_order_item(item, idx)

    @staticmethod
    def validate_order_item(item: OrderItemCreate, index: int) -> None:
        """
        Validate a single order item.
        
        Args:
            item: Order item schema
            index: Item index for error messaging
            
        Raises:
            OrderInvalidItemError: If item is invalid
        """
        # Validate quantity
        if item.quantity_ordered <= 0:
            raise OrderInvalidItemError(
                f"Item {index + 1}: Quantity must be positive"
            )
        
        # Validate unit price
        if item.unit_price <= 0:
            raise OrderInvalidItemError(
                f"Item {index + 1}: Unit price must be positive"
            )
        
        # Validate discount percentage
        if item.discount_percent < 0 or item.discount_percent > 100:
            raise OrderInvalidItemError(
                f"Item {index + 1}: Discount must be between 0 and 100"
            )

    @staticmethod
    def validate_inventory_availability(
        inventory_service, items: List[OrderItemCreate]
    ) -> None:
        """
        Validate inventory availability for all order items.
        
        Uses shared inventory service - no direct DB access.
        
        Args:
            inventory_service: Shared inventory service instance
            items: List of order items to validate
            
        Raises:
            OrderInsufficientInventoryError: If inventory is insufficient
        """
        for item in items:
            # Get product details from inventory service
            product = inventory_service.get_product_by_id(item.product_id)
            
            if not product:
                raise OrderInsufficientInventoryError(
                    product_code=f"PRODUCT_{item.product_id}",
                    required=item.quantity_ordered,
                    available=0,
                )
            
            # Check available stock
            available_qty = inventory_service.get_available_stock(
                product_id=item.product_id
            )
            
            if available_qty < item.quantity_ordered:
                raise OrderInsufficientInventoryError(
                    product_code=product.code,
                    required=item.quantity_ordered,
                    available=available_qty,
                )

    @staticmethod
    def validate_order_total(total_amount: Decimal, max_limit: Optional[Decimal] = None) -> None:
        """
        Validate order total amount.
        
        Args:
            total_amount: Order total to validate
            max_limit: Optional maximum allowed total
            
        Raises:
            OrderInvalidItemError: If total exceeds limits
        """
        if total_amount < 0:
            raise OrderInvalidItemError("Order total cannot be negative")
        
        if max_limit and total_amount > max_limit:
            raise OrderInvalidItemError(
                f"Order total {total_amount} exceeds maximum limit {max_limit}"
            )

    @staticmethod
    def validate_reason(reason: Optional[str], required: bool = False) -> None:
        """
        Validate reason field for state transitions.
        
        Args:
            reason: Reason text to validate
            required: Whether reason is mandatory
            
        Raises:
            OrderInvalidItemError: If reason is invalid
        """
        if required and not reason:
            raise OrderInvalidItemError("Reason is required for this action")
        
        if reason and len(reason) > 500:
            raise OrderInvalidItemError("Reason cannot exceed 500 characters")
