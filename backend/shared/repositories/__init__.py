"""
Shared repository layer base classes.

All database access must go through repository layer.
No raw SQL inside services.
"""

from typing import TypeVar, Generic, Optional, Any, Type
from datetime import datetime, timezone

from sqlalchemy.orm import Session, Query
from sqlalchemy import Column, Integer, DateTime, Boolean

from backend.core.exceptions import NotFoundError


T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.
    
    All repositories must inherit from this class.
    """
    
    def __init__(self, model: Type[T], session: Session) -> None:
        self.model = model
        self.session = session
    
    def get(self, entity_id: int) -> T:
        """Get entity by ID."""
        entity = self.session.query(self.model).filter(
            self.model.id == entity_id
        ).first()
        
        if not entity:
            raise NotFoundError(
                entity_type=self.model.__tablename__,
                entity_id=entity_id
            )
        
        return entity
    
    def get_optional(self, entity_id: int) -> Optional[T]:
        """Get entity by ID, returning None if not found."""
        return self.session.query(self.model).filter(
            self.model.id == entity_id
        ).first()
    
    def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[T]:
        """Get all entities with pagination."""
        return (
            self.session.query(self.model)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def create(self, data: dict[str, Any]) -> T:
        """Create new entity."""
        entity = self.model(**data)
        self.session.add(entity)
        self.session.flush()
        return entity
    
    def update(
        self,
        entity_id: int,
        data: dict[str, Any]
    ) -> T:
        """Update entity."""
        entity = self.get(entity_id)
        
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        self.session.flush()
        return entity
    
    def delete(self, entity_id: int) -> None:
        """Soft delete entity."""
        entity = self.get(entity_id)
        
        # Soft delete pattern
        if hasattr(entity, "deleted_at"):
            entity.deleted_at = datetime.now(timezone.utc)
        
        if hasattr(entity, "status"):
            entity.status = "deleted"
        
        self.session.flush()
    
    def count(self) -> int:
        """Count total entities."""
        return self.session.query(self.model).count()
    
    def exists(self, entity_id: int) -> bool:
        """Check if entity exists."""
        return self.session.query(self.model).filter(
            self.model.id == entity_id
        ).first() is not None
    
    def query(self) -> Query:
        """Get query builder for advanced queries."""
        return self.session.query(self.model)
