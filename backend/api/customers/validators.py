"""
Customer module validators.

Additional customer-specific validation rules.
"""

from core.exceptions import ValidationError
from shared.validation import ValidationEngine


class CustomerValidators:
    """Customer-specific validators."""
    
    @staticmethod
    def validate_email_domain(email: str) -> None:
        """Validate email domain format."""
        if "@" not in email:
            raise ValidationError("Invalid email format", field="email")
        
        domain = email.split("@")[1]
        if "." not in domain:
            raise ValidationError("Invalid email domain", field="email")
    
    @staticmethod
    def validate_credit_limit(credit_limit: float) -> None:
        """Validate credit limit is reasonable."""
        ValidationEngine.validate_non_negative_number(
            credit_limit,
            "credit_limit"
        )
        
        # Maximum credit limit check (configurable)
        max_limit = 10_000_000  # 10 million
        if credit_limit > max_limit:
            raise ValidationError(
                f"Credit limit cannot exceed {max_limit}",
                field="credit_limit"
            )
    
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
