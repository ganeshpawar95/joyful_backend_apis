from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core import security
from app.db.models.user import User, UserStatus
from app.schemas.request import UserCreate,UserResponse, UserUpdate
from app.schemas.response import B2BLoginResponse, TokenResponse
from app.services.user_service import (
    b2b_user_login, get_user_by_id, create_user, update_user
)
from app.db.session import get_db
from fastapi import HTTPException, status


router = APIRouter()


# Endpoint to generate new access token using refresh token
@router.post("/token/refresh")
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        user_id = security.verify_refresh_token(refresh_token, db)
        if user_id is None:
            raise ValueError("Invalid or expired refresh token.")
        return TokenResponse(
            access_token=security.create_access_token(user_id, timedelta(minutes=30)),
            refresh_token=security.create_refresh_token(user_id,timedelta(days=30)),
            id = user_id
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(error))


#login user B2B
@router.post("/b2B/login",response_model=TokenResponse)
async def login(data:B2BLoginResponse, db: Session = Depends(get_db)):
    user = b2b_user_login(session=db, email=data.email, phone=data.phone)    
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    elif user.status == UserStatus.INACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    
    return TokenResponse(
        access_token=security.create_access_token(
            user.id, expires_delta=timedelta(minutes=30)
        ),
        refresh_token=security.create_refresh_token(user.id,timedelta(days=30)),
        id = user.id
    )

# register user
@router.post("/register", response_model=UserResponse)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        if user.email and db.query(User).filter(User.email == user.email).scalar():
            raise ValueError("Email already exists.")

        # Check if phone already exists
        if user.phone and db.query(User).filter(User.phone == user.phone).scalar():
            raise ValueError("Phone already exists.")

        # Validate if either email or phone is provided
        UserCreate.validate_email_or_phone(user.email, user.phone)

        return create_user(db, user)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(error))

        
# update user
@router.put("/{user_id}", response_model=UserResponse)
def update_existing_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    try:
        updated_user = update_user(db, user_id, user)
        if not updated_user:
            raise ValueError("User not found")
        return updated_user
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(error))

#user details
@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        return user
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(error))

