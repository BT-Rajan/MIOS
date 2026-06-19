"""
Shared base models for all entities.

Provides common fields and behaviors across all modules.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class TimestampMixin:
    """Mixin for created/updated timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete pattern."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def mark_deleted(self) -> None:
        """Mark entity as deleted."""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_deleted = True


class VersionMixin:
    """Mixin for entity versioning."""
    
    version = Column(Integer, default=1, nullable=False)
    
    def increment_version(self) -> None:
        """Increment version number."""
        self.version = (self.version or 0) + 1


class CodeMixin:
    """Mixin for entity code field."""
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    @staticmethod
    def generate_code(prefix: str, value: int) -> str:
        """Generate standardized code."""
        return f"{prefix}-{value:06d}"
