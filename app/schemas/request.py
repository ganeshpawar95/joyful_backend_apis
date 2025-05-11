from sqlmodel import Field, SQLModel
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: int


class LoginRequest(SQLModel):
    email_phone: str
    password: str


class UserCreate(SQLModel):
    username: str = Field(nullable=False, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=15)
    password: str = Field(nullable=False, min_length=5, max_length=100)
    profile_pic: str = Field(default="", nullable=True)
    grade: str = Field(nullable=False, max_length=10)
    student_board: str = Field(nullable=False, max_length=50)
    country: str = Field(nullable=False, max_length=50)

    @staticmethod
    def validate_email_or_phone(email: str, phone: str):
        if not email and not phone:
            raise ValueError("Either email or phone must be provided.")
        return True

    class Config:
        validate_assignment = True


class UserResponse(SQLModel):
    id: int = 0
    username: str
    email: str = ("",)
    phone: str = ""
    profile_pic: str = ""
    grade: str
    student_board: str
    country: str


class UserUpdate(SQLModel):
    username: str
    email: str = ("",)
    phone: str = ""
    profile_pic: str = ""
    grade: str
    student_board: str
    country: str


class UpdateProductPayload(SQLModel):
    product_name: Optional[str] = None
    url_name: Optional[str] = None
    offer_price: Optional[int] = None
    price: Optional[int] = None
    care_instructions: Optional[str] = None
    delivery_info: Optional[str] = None
    meta_title: Optional[str] = None
    meta_keywords: Optional[str] = None
    meta_desc: Optional[str] = None
    description: Optional[str] = None


class AddToCartPayload(SQLModel):
    product_id: int
    session_id: str
    certificate_color: Optional[str] = None
    frame_color: Optional[str] = None
    frame_size: Optional[str] = None
    frame_thickness: Optional[str] = None
    tag_options: Optional[List[Dict[str, Any]]]


class OrderCreatePayload(BaseModel):
    username: str
    phone: str
    user_email: str
    user_fname: str
    user_lname: str
    user_address: str
    city: str
    landmark: Optional[str]
    state: str
    pincode: str
    country: str
    contact_mobile: str
    shipping_fee: int
    total_amount: int
    payment_id: str
