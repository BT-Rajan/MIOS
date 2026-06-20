"""Product module exceptions."""

from backend.core.exceptions import MIOSException


class ProductNotFoundException(MIOSException):
    """Product not found."""

    def __init__(self, product_id: int):
        super().__init__(f"Product {product_id} not found")


class ProductDuplicateCodeException(MIOSException):
    """Duplicate product code."""

    def __init__(self, code: str):
        super().__init__(f"Product code '{code}' already exists")


class BOMNotFoundException(MIOSException):
    """BOM not found."""

    def __init__(self, bom_id: int):
        super().__init__(f"BOM {bom_id} not found")


class BOMCircularReferenceException(MIOSException):
    """Circular reference in BOM."""

    def __init__(self, product_id: int):
        super().__init__(f"Circular reference detected for product {product_id}")


class BOMInvalidComponentException(MIOSException):
    """Invalid component in BOM."""

    def __init__(self, message: str):
        super().__init__(message)


class RoutingNotFoundException(MIOSException):
    """Routing not found."""

    def __init__(self, routing_id: int):
        super().__init__(f"Routing {routing_id} not found")


class ComponentNotFoundException(MIOSException):
    """Component not found."""

    def __init__(self, component_id: int):
        super().__init__(f"Component {component_id} not found")
