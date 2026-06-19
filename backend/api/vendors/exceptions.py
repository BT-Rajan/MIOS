"""
Vendor module exceptions.

Vendor-specific error types.
"""

from core.exceptions import MIOSException


class VendorError(MIOSException):
    """Base vendor exception."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class VendorNotFoundError(VendorError):
    """Vendor not found."""
    
    def __init__(self, vendor_id: int) -> None:
        super().__init__(f"Vendor {vendor_id} not found")


class VendorEmailExistsError(VendorError):
    """Vendor email already exists."""
    
    def __init__(self, email: str) -> None:
        super().__init__(f"Vendor with email {email} already exists")


class VendorCodeExistsError(VendorError):
    """Vendor code already exists."""
    
    def __init__(self, code: str) -> None:
        super().__init__(f"Vendor with code {code} already exists")


class VendorInactiveError(VendorError):
    """Vendor is inactive."""
    
    def __init__(self, vendor_id: int) -> None:
        super().__init__(f"Vendor {vendor_id} is inactive")

