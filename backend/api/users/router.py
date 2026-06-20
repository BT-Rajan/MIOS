"""User management router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.api.users.schemas import UserCreate, UserUpdate, UserResponse
from backend.api.users.service import UserService
from backend.shared.permissions.service import PermissionService

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: : Session,
    current_user: UserResponse = Depends(get_current_user)
):
    """List all users (admin only)."""
    # Check permission
    perm_service = PermissionService(db)
    if not perm_service.can(current_user.id, "manage_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    return user_service.get_all(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: : Session,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific user by ID."""
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: : Session,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new user (admin only)."""
    # Check permission
    perm_service = PermissionService(db)
    if not perm_service.can(current_user.id, "manage_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    try:
        user = user_service.create(user_data, actor_id=current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: : Session,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update an existing user."""
    # Check permission - user can update themselves or admin can update anyone
    perm_service = PermissionService(db)
    if not perm_service.can(current_user.id, "manage_users") and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    try:
        user = user_service.update(user_id, user_data, actor_id=current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: : Session,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a user (admin only)."""
    # Check permission
    perm_service = PermissionService(db)
    if not perm_service.can(current_user.id, "manage_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    try:
        user_service.delete(user_id, actor_id=current_user.id)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
