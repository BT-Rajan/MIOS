"""
Inventory exceptions for MIOS.
"""
from backend.core.exceptions import MIOSException


class InventoryException(MIOSException):
    """Base exception for inventory module."""
    pass


class WarehouseNotFound(InventoryException):
    """Raised when warehouse is not found."""
    def __init__(self, warehouse_id: int):
        super().__init__(f"Warehouse with ID {warehouse_id} not found")


class WarehouseCodeExists(InventoryException):
    """Raised when warehouse code already exists."""
    def __init__(self, code: str):
        super().__init__(f"Warehouse with code '{code}' already exists")


class StockItemNotFound(InventoryException):
    """Raised when stock item is not found."""
    def __init__(self, product_id: int, warehouse_id: int):
        super().__init__(
            f"Stock item for product {product_id} in warehouse {warehouse_id} not found"
        )


class InsufficientStock(InventoryException):
    """Raised when insufficient stock is available."""
    def __init__(
        self,
        product_id: int,
        warehouse_id: int,
        requested: float,
        available: float
    ):
        super().__init__(
            f"Insufficient stock for product {product_id} in warehouse {warehouse_id}. "
            f"Requested: {requested}, Available: {available}"
        )


class InvalidMovementType(InventoryException):
    """Raised when movement type is invalid for the operation."""
    def __init__(self, movement_type: str, operation: str):
        super().__init__(
            f"Invalid movement type '{movement_type}' for operation '{operation}'"
        )


class ReservationNotFound(InventoryException):
    """Raised when stock reservation is not found."""
    def __init__(self, reservation_id: int):
        super().__init__(f"Stock reservation with ID {reservation_id} not found")


class ReservationExpired(InventoryException):
    """Raised when stock reservation has expired."""
    def __init__(self, reservation_id: int):
        super().__init__(f"Stock reservation {reservation_id} has expired")


class NegativeStockError(InventoryException):
    """Raised when operation would result in negative stock."""
    def __init__(self, product_id: int, warehouse_id: int):
        super().__init__(
            f"Operation would result in negative stock for product {product_id} "
            f"in warehouse {warehouse_id}"
        )
