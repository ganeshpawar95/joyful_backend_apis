from datetime import datetime
from enum import IntEnum
from typing import Optional
from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UserStatus(IntEnum):
    ACTIVE = 1
    INACTIVE = 2


class User(ItemBase, table=True):  # Use table=True to indicate this is a table
    __tablename__ = "users"  # Optional, automatically inferred from the class name
    username: str = Field(nullable=False, index=True, min_length=3, max_length=50)
    email: str = Field(nullable=True, index=True)
    phone: str = Field(nullable=True, index=True, max_length=100)
    password: str = Field(nullable=True, min_length=5, max_length=100)
    profile_pic: str = Field(nullable=True, default="")
    status: str = Field(nullable=False, index=True, max_length=50)


class User_shipping_address(
    ItemBase, table=True
):  # Use table=True to indicate this is a table
    __tablename__ = (
        "user_shipping_address"  # Optional, automatically inferred from the class name
    )
    user_email: str = Field(nullable=False, index=True)
    user_fname: str = Field(nullable=True, index=True, max_length=100)
    user_lname: str = Field(nullable=True, index=True, max_length=100)
    user_address: str = Field(nullable=False)
    city: str = Field(nullable=True, default="")
    landmark: str = Field(nullable=True, default="")
    state: str = Field(nullable=False, index=True)
    pincode: str = Field(nullable=False, index=True, max_length=50)
    country: str = Field(nullable=False, index=True)
    contact_mobile: str = Field(nullable=False, index=True)


class SettingsModel(ItemBase, table=True):  # Use table=True to indicate this is a table
    __tablename__ = "settings"  # Optional, automatically inferred from the class name
    pricesWithTax: str = Field(nullable=False, index=True, default=False)
    pricesWithShipping: str = Field(default=False, nullable=True, index=True)
    taxRate: int = Field(default=0, nullable=True, index=True)
    shippingCharges: int = Field(default=0, nullable=True, index=True)
