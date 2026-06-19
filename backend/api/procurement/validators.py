"""
Validators for procurement module.

Reusable validation functions using shared ValidationEngine.
"""

from decimal import Decimal
from typing import Optional, List
from datetime import datetime

from backend.shared.validation.engine import ValidationEngine
from backend.api.procurement.exceptions import (
    InsufficientApprovalAuthority,
)


class ProcurementValidators:
    """Reusable validators for procurement operations."""

    @staticmethod
    def validate_positive_quantity(value: Decimal, field_name: str = "quantity") -> None:
        """Validate quantity is positive."""
        ValidationEngine.validate_positive_number(value, field_name)

    @staticmethod
    def validate_non_negative_price(value: Decimal, field_name: str = "price") -> None:
        """Validate price is non-negative."""
        if value < 0:
            raise ValueError(f"{field_name} cannot be negative")

    @staticmethod
    def validate_required_date(value: Optional[datetime], field_name: str = "date") -> None:
        """Validate date is provided."""
        if value is None:
            raise ValueError(f"{field_name} is required")

    @staticmethod
    def validate_future_date(value: datetime, field_name: str = "date") -> None:
        """Validate date is in the future."""
        if value <= datetime.now():
            raise ValueError(f"{field_name} must be in the future")

    @staticmethod
    def validate_priority(priority: str) -> None:
        """Validate priority value."""
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            raise ValueError(
                f"Invalid priority: {priority}. Must be one of {valid_priorities}"
            )

    @staticmethod
    def validate_currency(currency: str) -> None:
        """Validate currency code."""
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("Invalid currency code. Must be 3 letters.")

    @staticmethod
    def validate_approval_authority(
        amount: Decimal,
        user_approval_limit: Decimal
    ) -> None:
        """
        Validate user has approval authority for amount.
        
        Args:
            amount: Transaction amount
            user_approval_limit: User's maximum approval limit
            
        Raises:
            InsufficientApprovalAuthority: If amount exceeds limit
        """
        if amount > user_approval_limit:
            raise InsufficientApprovalAuthority(
                amount=float(amount),
                user_limit=float(user_approval_limit)
            )

    @staticmethod
    def validate_items_not_empty(items: List) -> None:
        """Validate items list is not empty."""
        if not items or len(items) == 0:
            raise ValueError("At least one item is required")

    @staticmethod
    def validate_received_quantity(
        quantity_received: Decimal,
        quantity_expected: Decimal
    ) -> None:
        """Validate received quantity does not exceed expected."""
        if quantity_received > quantity_expected:
            raise ValueError(
                f"Received quantity {quantity_received} exceeds "
                f"expected {quantity_expected}"
            )

    @staticmethod
    def validate_rejection_reason(reason: Optional[str]) -> None:
        """Validate rejection reason is provided."""
        if not reason or len(reason.strip()) == 0:
            raise ValueError("Rejection reason is required")
