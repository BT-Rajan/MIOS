"""
Custom exception classes for MIOS.
"""

from typing import Optional, Any


class MIOSException(Exception):
    """Base exception for MIOS."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MIOSException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(message=message, status_code=400, details=details)


class NotFoundError(MIOSException):
    """Raised when entity not found."""
    
    def __init__(self, entity_type: str, entity_id: Any) -> None:
        message = f"{entity_type} with id {entity_id} not found"
        details = {"entity_type": entity_type, "entity_id": entity_id}
        super().__init__(message=message, status_code=404, details=details)


class ForbiddenError(MIOSException):
    """Raised when action is forbidden."""
    
    def __init__(self, message: str = "Action forbidden") -> None:
        super().__init__(message=message, status_code=403)


class ConflictError(MIOSException):
    """Raised when conflict detected."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=409)


class WorkflowError(MIOSException):
    """Raised when workflow transition invalid."""
    
    def __init__(
        self,
        entity_type: str,
        from_state: str,
        to_state: str
    ) -> None:
        message = (
            f"Invalid workflow transition for {entity_type}: "
            f"cannot go from '{from_state}' to '{to_state}'"
        )
        details = {
            "entity_type": entity_type,
            "from_state": from_state,
            "to_state": to_state
        }
        super().__init__(message=message, status_code=400, details=details)


class AuditError(MIOSException):
    """Raised when audit logging fails."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)


class AuthenticationError(MIOSException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, status_code=401)
