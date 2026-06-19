"""
Inventory validators for MIOS.

Reusable validation functions using the shared ValidationEngine.
"""
from decimal import Decimal
from typing import Optional, Tuple

from backend.shared.validation.engine import ValidationEngine, ValidationResult


class InventoryValidators:
    """Reusable inventory validators."""
    
    @staticmethod
    def validate_positive_quantity(value: Decimal) -> ValidationResult:
        """Validate that quantity is positive."""
        if value <= 0:
            return ValidationResult(
                valid=False,
                error="Quantity must be positive"
            )
        return ValidationResult(valid=True)
    
    @staticmethod
    def validate_non_negative_quantity(value: Decimal) -> ValidationResult:
        """Validate that quantity is non-negative."""
        if value < 0:
            return ValidationResult(
                valid=False,
                error="Quantity cannot be negative"
            )
        return ValidationResult(valid=True)
    
    @staticmethod
    def validate_sufficient_stock(
        available: Decimal,
        requested: Decimal
    ) -> ValidationResult:
        """Validate sufficient stock is available."""
        if requested > available:
            return ValidationResult(
                valid=False,
                error=f"Insufficient stock. Available: {available}, Requested: {requested}"
            )
        return ValidationResult(valid=True)
    
    @staticmethod
    def validate_warehouse_code(code: str) -> ValidationResult:
        """Validate warehouse code format."""
        if not code or len(code.strip()) == 0:
            return ValidationResult(
                valid=False,
                error="Warehouse code is required"
            )
        if len(code) > 50:
            return ValidationResult(
                valid=False,
                error="Warehouse code must not exceed 50 characters"
            )
        return ValidationResult(valid=True)
    
    @staticmethod
    def validate_warehouse_name(name: str) -> ValidationResult:
        """Validate warehouse name."""
        if not name or len(name.strip()) == 0:
            return ValidationResult(
                valid=False,
                error="Warehouse name is required"
            )
        if len(name) > 200:
            return ValidationResult(
                valid=False,
                error="Warehouse name must not exceed 200 characters"
            )
        return ValidationResult(valid=True)
    
    @staticmethod
    def validate_movement_reason(
        movement_type: str,
        reason: Optional[str]
    ) -> ValidationResult:
        """Validate that adjustment movements have a reason."""
        if movement_type == "adjustment" and not reason:
            return ValidationResult(
                valid=False,
                error="Reason is required for stock adjustments"
            )
        return ValidationResult(valid=True)
    
    @staticmethod
    def validate_reservation_expiry(
        expires_at: Optional[Decimal],
        operation: str = "create"
    ) -> ValidationResult:
        """Validate reservation expiry date."""
        # Implementation depends on business rules
        return ValidationResult(valid=True)
    
    @classmethod
    def validate_stock_item_creation(
        cls,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """Validate stock item creation parameters."""
        if product_id <= 0:
            return False, "Invalid product ID"
        if warehouse_id <= 0:
            return False, "Invalid warehouse ID"
        
        result = cls.validate_non_negative_quantity(quantity)
        if not result.valid:
            return False, result.error
        
        return True, None
    
    @classmethod
    def validate_stock_movement(
        cls,
        movement_type: str,
        quantity: Decimal,
        reason: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate stock movement parameters."""
        valid_types = [
            "receipt", "issue", "transfer",
            "adjustment", "return", "reservation", "release"
        ]
        
        if movement_type not in valid_types:
            return False, f"Invalid movement type. Must be one of: {valid_types}"
        
        result = cls.validate_positive_quantity(quantity)
        if not result.valid:
            return False, result.error
        
        result = cls.validate_movement_reason(movement_type, reason)
        if not result.valid:
            return False, result.error
        
        return True, None
