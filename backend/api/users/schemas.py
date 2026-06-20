"""User schemas for validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    
    username: Optional[str] = None
    user_id: Optional[int] = None
