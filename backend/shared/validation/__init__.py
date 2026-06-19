"""
Reusable validation engine.

Centralized validators used across all modules.
No duplicated validations allowed.
"""

from typing import Optional, Any
from decimal import Decimal

from backend.core.exceptions import ValidationError


class ValidationEngine:
    """
    Central validation engine with reusable validators.
    
    All modules must use these validators instead of 
    implementing their own validation logic.
    """
    
    @staticmethod
    def validate_positive_number(
        value: Any,
        field_name: str = "value"
    ) -> None:
        """Validate that a number is positive."""
        try:
            num = Decimal(str(value))
            if num <= 0:
                raise ValidationError(
                    f"{field_name} must be positive",
                    field=field_name
                )
        except (TypeError, ValueError):
            raise ValidationError(
                f"{field_name} must be a valid number",
                field=field_name
            )
    
    @staticmethod
    def validate_non_negative_number(
        value: Any,
        field_name: str = "value"
    ) -> None:
        """Validate that a number is non-negative."""
        try:
            num = Decimal(str(value))
            if num < 0:
                raise ValidationError(
                    f"{field_name} cannot be negative",
                    field=field_name
                )
        except (TypeError, ValueError):
            raise ValidationError(
                f"{field_name} must be a valid number",
                field=field_name
            )
    
    @staticmethod
    def validate_required_field(
        value: Any,
        field_name: str
    ) -> None:
        """Validate that a required field is not empty."""
        if value is None or value == "":
            raise ValidationError(
                f"{field_name} is required",
                field=field_name
            )
        
        if isinstance(value, str) and not value.strip():
            raise ValidationError(
                f"{field_name} cannot be empty",
                field=field_name
            )
    
    @staticmethod
    def validate_reason_required(
        reason: Optional[str],
        action: str
    ) -> None:
        """Validate that a reason is provided for sensitive actions."""
        if not reason or not reason.strip():
            raise ValidationError(
                f"Reason is required for {action}",
                field="reason"
            )
        
        if len(reason.strip()) < 10:
            raise ValidationError(
                "Reason must be at least 10 characters",
                field="reason"
            )
    
    @staticmethod
    def validate_string_length(
        value: str,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> None:
        """Validate string length constraints."""
        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} must be a string",
                field=field_name
            )
        
        if min_length is not None and len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                field=field_name
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"{field_name} cannot exceed {max_length} characters",
                field=field_name
            )
    
    @staticmethod
    def validate_percentage(
        value: Any,
        field_name: str = "percentage"
    ) -> None:
        """Validate that a value is a valid percentage (0-100)."""
        try:
            num = Decimal(str(value))
            if num < 0 or num > 100:
                raise ValidationError(
                    f"{field_name} must be between 0 and 100",
                    field=field_name
                )
        except (TypeError, ValueError):
            raise ValidationError(
                f"{field_name} must be a valid number",
                field=field_name
            )
    
    @staticmethod
    def validate_entity_id(
        entity_id: Any,
        entity_type: str
    ) -> None:
        """Validate entity ID is positive integer."""
        if not isinstance(entity_id, int) or entity_id <= 0:
            raise ValidationError(
                f"Invalid {entity_type} ID",
                field=f"{entity_type}_id"
            )
    
    @staticmethod
    def validate_code_format(
        code: str,
        field_name: str = "code"
    ) -> None:
        """Validate code format (alphanumeric, no spaces)."""
        if not isinstance(code, str):
            raise ValidationError(
                f"{field_name} must be a string",
                field=field_name
            )
        
        if not code.replace("_", "").replace("-", "").isalnum():
            raise ValidationError(
                f"{field_name} must be alphanumeric",
                field=field_name
            )
        
        if " " in code:
            raise ValidationError(
                f"{field_name} cannot contain spaces",
                field=field_name
            )
