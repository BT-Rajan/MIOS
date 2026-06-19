"""
System-wide constants for MIOS.
"""

from enum import Enum


class EntityState(str, Enum):
    """Generic entity states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class WorkflowStatus(str, Enum):
    """Generic workflow status values."""
    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditAction(str, Enum):
    """Standard audit actions."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    APPROVED = "approved"
    REJECTED = "rejected"
    TRANSITIONED = "transitioned"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class PermissionType(str, Enum):
    """Permission types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class EventType(str, Enum):
    """Event bus event types."""
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"
    WORKFLOW_TRANSITIONED = "workflow.transitioned"
    APPROVAL_REQUIRED = "approval.required"
    INVENTORY_LOW = "inventory.low"
    ORDER_DELAYED = "order.delayed"
