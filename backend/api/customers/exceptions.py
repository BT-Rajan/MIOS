"""
Customer module exceptions.

Customer-specific error types.
"""

from backend.core.exceptions import MIOSException


class CustomerError(MIOSException):
    """Base customer exception."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class CustomerNotFoundError(CustomerError):
    """Customer not found."""
    
    def __init__(self, customer_id: int) -> None:
        super().__init__(f"Customer {customer_id} not found")


class CustomerEmailExistsError(CustomerError):
    """Customer email already exists."""
    
    def __init__(self, email: str) -> None:
        super().__init__(f"Customer with email {email} already exists")


class CustomerCodeExistsError(CustomerError):
    """Customer code already exists."""
    
    def __init__(self, code: str) -> None:
        super().__init__(f"Customer with code {code} already exists")


class CustomerInactiveError(CustomerError):
    """Customer is inactive."""
    
    def __init__(self, customer_id: int) -> None:
        super().__init__(f"Customer {customer_id} is inactive")
