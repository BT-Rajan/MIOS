"""
Custom exceptions for Order module.

Extends base MIOSException with order-specific error types.
"""

from backend.core.exceptions import MIOSException


class OrderException(MIOSException):
    """Base exception for order-related errors."""

    pass


class OrderNotFoundException(OrderException):
    """Raised when an order is not found."""

    def __init__(self, order_id: int | str):
        super().__init__(f"Order not found: {order_id}")


class OrderInvalidStatusTransitionError(OrderException):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, from_status: str, to_status: str):
        super().__init__(
            f"Invalid status transition from '{from_status}' to '{to_status}'"
        )


class OrderAlreadySubmittedError(OrderException):
    """Raised when attempting to modify a submitted order."""

    def __init__(self, order_number: str):
        super().__init__(f"Order {order_number} is already submitted and cannot be modified")


class OrderAlreadyApprovedError(OrderException):
    """Raised when attempting to approve an already approved order."""

    def __init__(self, order_number: str):
        super().__init__(f"Order {order_number} is already approved")


class OrderAlreadyRejectedError(OrderException):
    """Raised when attempting to act on a rejected order."""

    def __init__(self, order_number: str):
        super().__init__(f"Order {order_number} has been rejected")


class OrderAlreadyCancelledError(OrderException):
    """Raised when attempting to cancel an already cancelled order."""

    def __init__(self, order_number: str):
        super().__init__(f"Order {order_number} is already cancelled")


class OrderDuplicateNumberError(OrderException):
    """Raised when a duplicate order number is detected."""

    def __init__(self, order_number: str):
        super().__init__(f"Order number {order_number} already exists")


class OrderInsufficientInventoryError(OrderException):
    """Raised when inventory is insufficient for order items."""

    def __init__(self, product_code: str, required: int, available: int):
        super().__init__(
            f"Insufficient inventory for {product_code}: "
            f"required {required}, available {available}"
        )


class OrderInvalidItemError(OrderException):
    """Raised when an order item is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class OrderCannotShipCompleteError(OrderException):
    """Raised when order cannot be shipped completely."""

    def __init__(self, order_number: str):
        super().__init__(f"Order {order_number} cannot be shipped completely")


class OrderProductionNotCompleteError(OrderException):
    """Raised when attempting to ship before production is complete."""

    def __init__(self, order_number: str):
        super().__init__(f"Order {order_number} production is not complete")
