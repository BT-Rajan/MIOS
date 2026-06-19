"""
Central RBAC permission engine.

All modules must use this engine for authorization checks.
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, Session, declarative_base

from backend.core.exceptions import ForbiddenError
from backend.core.constants import PermissionType


Base = declarative_base()

# Association tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True)
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True)
)


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(Base):
    """Role model."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )


class Permission(Base):
    """Permission model."""
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class PermissionEngine:
    """
    Central permission engine for RBAC.
    
    All modules must use this engine for authorization checks.
    """
    
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def can(
        self,
        user_id: int,
        action: str,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission to perform action.
        
        Args:
            user_id: ID of the user
            action: Action type (e.g., 'approve_order', 'create')
            resource: Optional resource type (e.g., 'order', 'inventory')
            
        Returns:
            True if user has permission
        """
        user = self.session.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return False
        
        # Check all roles for required permission
        for role in user.roles:
            for perm in role.permissions:
                # Exact match
                if perm.name == action:
                    return True
                
                # Resource-action pattern
                if resource and perm.resource == resource:
                    if perm.action == action:
                        return True
        
        return False
    
    def can_any(
        self,
        user_id: int,
        actions: list[str],
        resource: Optional[str] = None
    ) -> bool:
        """Check if user has any of the specified permissions."""
        for action in actions:
            if self.can(user_id, action, resource):
                return True
        return False
    
    def must(
        self,
        user_id: int,
        action: str,
        resource: Optional[str] = None,
        message: str = "Action forbidden"
    ) -> None:
        """
        Enforce permission check, raising exception if denied.
        
        Args:
            user_id: ID of the user
            action: Action type
            resource: Optional resource type
            message: Custom error message
            
        Raises:
            ForbiddenError: If permission denied
        """
        if not self.can(user_id, action, resource):
            raise ForbiddenError(message)
    
    def get_user_permissions(self, user_id: int) -> list[str]:
        """Get all permission names for a user."""
        user = self.session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return []
        
        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        
        return list(permissions)
    
    def create_permission(
        self,
        name: str,
        resource: str,
        action: str
    ) -> Permission:
        """Create a new permission."""
        permission = Permission(
            name=name,
            resource=resource,
            action=action
        )
        
        self.session.add(permission)
        return permission
    
    def create_role(self, name: str, description: str) -> Role:
        """Create a new role."""
        role = Role(name=name, description=description)
        self.session.add(role)
        return role
    
    def assign_role_to_user(
        self,
        user_id: int,
        role_id: int
    ) -> None:
        """Assign a role to a user."""
        user = self.session.query(User).filter(User.id == user_id).first()
        role = self.session.query(Role).filter(Role.id == role_id).first()
        
        if not user or not role:
            raise ValueError("User or role not found")
        
        if role not in user.roles:
            user.roles.append(role)
