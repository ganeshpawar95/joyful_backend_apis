from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel

from sqlmodel import SQLModel


# Generic message
class Message(SQLModel):
    message: str


class UserPublic(SQLModel):
    id: int = 0
    username: str
    email: str = ("",)
    phone: str = ""
    profile_pic: str = ""
    grade: str
    student_board: str
    country: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    id: int


class B2BLoginResponse(SQLModel):
    email: str
    password: str


class NotificationPublic(BaseModel):
    id: int
    receiver_user_id: int
    sender_user_id: Optional[int] = None
    message: str
    payload: Optional[Dict[str, Any]] = None
    sender: Optional["UserPublic"] = None
    action: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# --------------------------------new payload-----------------------------


class MessageResponse(SQLModel):
    message: str = ""


class ProductImageResponse(BaseModel):
    id: int
    images: Optional[str]  # Allow NULL values
    status: str
    priority: int


class ProductTagOptionsResponse(BaseModel):
    id: int
    name: Optional[str]  # Allow NULL values
    tag: str
    priority: int
    tag_optional: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True


class ProductColorResponse(BaseModel):
    id: int
    priority: int
    name: Optional[str]  # Allow NULL values


class ProductRatingResponse(BaseModel):
    id: int
    user_name: str
    title: Optional[str] = None
    review: Optional[str] = None
    rating: int
    status: str


# Product Response Model (with all fields from Products)
class ProductResponse(BaseModel):
    id: int
    product_name: Optional[str]
    url_name: Optional[str]
    thumbnail: str
    offer_price: Optional[str]
    price: Optional[str]
    description: Optional[str]
    care_instructions: Optional[str]
    delivery_info: Optional[str]
    meta_title: Optional[str]
    meta_keywords: Optional[str]
    meta_desc: Optional[str]
    status: Optional[bool]
    priority: Optional[int]
    product_type: Optional[str]
    product_trading_type: Optional[str]

    # Include Product Images Relationship
    product_images: List[ProductImageResponse] = []
    product_ratings: List[ProductRatingResponse] = []  # List of ratings
    product_tag_options: List[ProductTagOptionsResponse] = []  # List of ratings

    certificate_colors: List[ProductColorResponse] = []  # List of ratings
    frame_colors: List[ProductColorResponse] = []  # List of ratings
    frame_size: List[ProductColorResponse] = []  # List of ratings
    frame_thickness: List[ProductColorResponse] = []  # List of ratings

    class Config:
        from_attributes = True  # Enables ORM conversion


# Pydantic Model for Request
class ProductReviewCreate(BaseModel):
    product_id: int
    user_name: Optional[str] = None
    title: Optional[str] = None
    review: Optional[str] = None
    rating: int
    status: str  # Example: "approved", "pending"


class ProductFrameCreate(BaseModel):
    name: Optional[str] = None
    status: bool  # Example: "approved", "pending"
    priority: Optional[int] = None
    product_id: int


class ProductTagCreate(BaseModel):
    product_id: int
    name: Optional[str] = None
    tag: Optional[str] = None
    validation_img: Optional[str] = ""
    priority: int  # Example: "approved", "pending"
    tag_optional: Optional[Dict[str, Any]]


# --- Pydantic Response Models ---
class TagOptionResponse(BaseModel):
    tag_name: str
    tag_data: str


class CartDetailsResponse(BaseModel):
    cart_id: int
    product_id: int
    is_digital: bool
    product_name: str
    price: int
    thumbnail: str
