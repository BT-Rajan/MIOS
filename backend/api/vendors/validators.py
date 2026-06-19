"""
Vendor module validators.

Additional vendor-specific validation rules.
"""

from core.exceptions import ValidationError
from shared.validation import ValidationEngine


class VendorValidators:
    """Vendor-specific validators."""
    
    @staticmethod
    def validate_email_domain(email: str) -> None:
        """Validate email domain format."""
        if "@" not in email:
            raise ValidationError("Invalid email format", field="email")
        
        domain = email.split("@")[1]
        if "." not in domain:
            raise ValidationError("Invalid email domain", field="email")
    
    @staticmethod
    def validate_payment_terms(days: int) -> None:
        """Validate payment terms are within acceptable range."""
        if days < 0:
            raise ValidationError(
                "Payment terms cannot be negative",
                field="payment_terms_days"
            )
        
        if days > 365:
            raise ValidationError(
                "Payment terms cannot exceed 365 days",
                field="payment_terms_days"
            )
    
    @staticmethod
    def validate_minimum_order(value: float) -> None:
        """Validate minimum order value is reasonable."""
        ValidationEngine.validate_non_negative_number(
            value,
            "minimum_order_value"
        )
        
        # Maximum minimum order check (configurable)
        max_value = 1_000_000  # 1 million
        if value > max_value:
            raise ValidationError(
                f"Minimum order cannot exceed {max_value}",
                field="minimum_order_value"
            )
    
    @staticmethod
    def validate_rating(rating: float) -> None:
        """Validate rating is within 0-5 range."""
        if rating < 0 or rating > 5:
            raise ValidationError(
                "Rating must be between 0 and 5",
                field="rating"
            )
    
    @staticmethod
    def validate_postal_code(postal_code: str, country: str) -> None:
        """Validate postal code format based on country."""
        if not postal_code:
            return
        
        # Basic validation - can be extended per country
        if len(postal_code) < 3 or len(postal_code) > 20:
            raise ValidationError(
                "Invalid postal code length",
                field="postal_code"
            )

