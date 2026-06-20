"""User service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from backend.api.users.models import User
from backend.api.users.repository import UserRepository
from backend.api.users.schemas import UserCreate, UserUpdate
from backend.core.security import get_password_hash
from backend.shared.audit.service import AuditService


class UserService:
    """Service for user business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
        self.audit_service = AuditService(db)
    
    def get(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return self.repository.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.repository.get_by_username(username)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return self.repository.get_all(skip=skip, limit=limit)
    
    def create(self, user_data: UserCreate, actor_id: int) -> User:
        """Create a new user."""
        # Check if username exists
        existing = self.repository.get_by_username(user_data.username)
        if existing:
            raise ValueError("Username already exists")
        
        # Check if email exists
        existing = self.repository.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        user = self.repository.create(user_data, hashed_password)
        
        # Audit log
        self.audit_service.record_event(
            entity_type="user",
            entity_id=user.id,
            action="created",
            actor_id=actor_id,
            old_state=None,
            new_state={"username": user.username, "email": user.email},
            reason="User account created"
        )
        
        return user
    
    def update(self, user_id: int, user_data: UserUpdate, actor_id: int) -> User:
        """Update an existing user."""
        user = self.repository.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        old_state = {
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
        
        # Hash password if provided
        if user_data.password:
            user_data.password = get_password_hash(user_data.password)
        
        updated_user = self.repository.update(user, user_data)
        
        new_state = {
            "username": updated_user.username,
            "email": updated_user.email,
            "is_active": updated_user.is_active
        }
        
        # Audit log
        self.audit_service.record_event(
            entity_type="user",
            entity_id=user.id,
            action="updated",
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            reason="User account updated"
        )
        
        return updated_user
    
    def delete(self, user_id: int, actor_id: int) -> None:
        """Soft delete a user."""
        user = self.repository.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        old_state = {"is_active": user.is_active}
        
        self.repository.delete(user)
        
        # Audit log
        self.audit_service.record_event(
            entity_type="user",
            entity_id=user_id,
            action="deleted",
            actor_id=actor_id,
            old_state=old_state,
            new_state={"is_active": False},
            reason="User account deactivated"
        )
