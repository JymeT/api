from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.logging import logger
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create a new user.
    """
    # Check if user with the same email exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        logger.warning(f"Attempt to create user with existing email: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if user with the same phone exists
    user = db.query(User).filter(User.phone == user_in.phone).first()
    if user:
        logger.warning(f"Attempt to create user with existing phone: {user_in.phone}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )
    
    # Create new user
    db_user = User(
        name=user_in.name,
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user created: {db_user.id}")
    return db_user


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user.
    """
    # Check if email is being updated and if it's already taken
    if user_in.email and user_in.email != current_user.email:
        user = db.query(User).filter(User.email == user_in.email).first()
        if user:
            logger.warning(f"User {current_user.id} attempted to update to an existing email: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Check if phone is being updated and if it's already taken
    if user_in.phone and user_in.phone != current_user.phone:
        user = db.query(User).filter(User.phone == user_in.phone).first()
        if user:
            logger.warning(f"User {current_user.id} attempted to update to an existing phone: {user_in.phone}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )
    
    # Update user data
    if user_in.name:
        current_user.name = user_in.name
    if user_in.email:
        current_user.email = user_in.email
    if user_in.phone:
        current_user.phone = user_in.phone
    if user_in.password:
        current_user.hashed_password = get_password_hash(user_in.password)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User {current_user.id} updated their profile")
    return current_user 