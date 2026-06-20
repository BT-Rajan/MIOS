"""Permission service for RBAC operations."""

from sqlalchemy.orm import Session
from typing import List, Optional

from backend.shared.permissions import PermissionEngine, User, Role, Permission


class PermissionService:
    """Service for permission and role management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.engine = PermissionEngine(db)
    
    def can(self, user_id: int, action: str, resource: Optional[str] = None) -> bool:
        """Check if user has permission."""
        return self.engine.can(user_id, action, resource)
    
    def must(self, user_id: int, action: str, resource: Optional[str] = None, message: str = "Action forbidden") -> None:
        """Enforce permission check."""
        self.engine.must(user_id, action, resource, message)
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user."""
        return self.engine.get_user_permissions(user_id)
    
    def create_permission(self, name: str, resource: str, action: str) -> Permission:
        """Create a new permission."""
        return self.engine.create_permission(name, resource, action)
    
    def create_role(self, name: str, description: str) -> Role:
        """Create a new role."""
        return self.engine.create_role(name, description)
    
    def assign_role_to_user(self, user_id: int, role_id: int) -> None:
        """Assign a role to a user."""
        self.engine.assign_role_to_user(user_id, role_id)
