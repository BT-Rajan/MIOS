"""Product module validators."""

from typing import Any, Dict

from backend.shared.validation import ValidationEngine


def validate_product_code(code: str) -> None:
    """Validate product code format."""
    if not code or len(code.strip()) == 0:
        raise ValueError("Product code cannot be empty")
    if len(code) > 50:
        raise ValueError("Product code cannot exceed 50 characters")


def validate_product_name(name: str) -> None:
    """Validate product name."""
    if not name or len(name.strip()) == 0:
        raise ValueError("Product name cannot be empty")
    if len(name) > 200:
        raise ValueError("Product name cannot exceed 200 characters")


def validate_positive_quantity(quantity: float) -> None:
    """Validate quantity is positive."""
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")


def validate_bom_quantity(quantity: float) -> None:
    """Validate BOM component quantity."""
    if quantity <= 0:
        raise ValueError("BOM component quantity must be positive")


def validate_routing_sequence(sequence: int) -> None:
    """Validate routing operation sequence."""
    if sequence < 1:
        raise ValueError("Routing sequence must be at least 1")


def validate_cost(cost: float) -> None:
    """Validate cost value."""
    if cost < 0:
        raise ValueError("Cost cannot be negative")
