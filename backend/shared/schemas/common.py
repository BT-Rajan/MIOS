"""
Shared Pydantic schemas for API request/response validation.

Used across all modules for consistent data validation.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class PaginationParams(BaseSchema):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and limit."""
        return (self.page - 1) * self.limit


class PaginationResponse(BaseSchema):
    """Pagination metadata in responses."""
    
    total: int
    page: int
    limit: int
    pages: int


class BaseResponse(BaseSchema):
    """Standard API response wrapper."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class AuditRecord(BaseSchema):
    """Audit log record schema."""
    
    id: int
    correlation_id: str
    entity_type: str
    entity_id: int
    action: str
    actor_id: int
    old_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    timestamp: datetime


class UserBase(BaseSchema):
    """Base user schema."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """User response schema."""
    
    id: int
    is_active: bool
    created_at: datetime


class RoleBase(BaseSchema):
    """Base role schema."""
    
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    
    id: int
    created_at: datetime
