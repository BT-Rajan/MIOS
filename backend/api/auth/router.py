"""Authentication router for user login and registration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core.security import authenticate_user, create_access_token, get_current_user
from api.users.schemas import UserCreate, UserResponse, Token
from api.users.service import UserService
from shared.permissions.service import PermissionService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user_service = UserService(db)
    
    # Create user (actor_id is 0 for registration since no user is logged in yet)
    try:
        user = user_service.create(user_data, actor_id=0)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user
