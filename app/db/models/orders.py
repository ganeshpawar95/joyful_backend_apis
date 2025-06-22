from datetime import datetime
from enum import IntEnum
from typing import Optional

from sqlalchemy import Column
from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON


class ItemBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class order_selected_tags(
    ItemBase, table=True
):  # Use table=True to indicate this is a table
    __tablename__ = (
        "user_selected_tags"  # Optional, automatically inferred from the class name
    )
    product_id: int = Field(foreign_key="products.id", nullable=False)
    order_id: int = Field(foreign_key="orders.id", nullable=True)
    cart_id: int = Field(foreign_key="carts.id", nullable=True)
    tag_name: str = Field(nullable=False, index=True)
    tag_data: str = Field(nullable=True, index=True, max_length=100)


class Order_details(ItemBase, table=True):  # Use table=True to indicate this is a table
    __tablename__ = (
        "order_details"  # Optional, automatically inferred from the class name
    )
    amount: int = Field(nullable=True, index=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    quantity: int = Field(nullable=True, index=True)
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    certificate_color: str = Field(nullable=False, index=True)
    frame_color: str = Field(nullable=False, index=True)
    frame_size: str = Field(nullable=False, index=True)
    frame_thickness: str = Field(nullable=False, index=True)


class Orders_status(ItemBase, table=True):
    __tablename__ = (
        "order_status"  # Optional, automatically inferred from the class name
    )
    user_id: int = Field(foreign_key="users.id", nullable=False)
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    order_status: str = Field(nullable=True, index=True)


class Orders(ItemBase, table=True):
    __tablename__ = "orders"  # Optional, automatically inferred from the class name
    user_id: int = Field(foreign_key="users.id", nullable=False)
    txn_id: str = Field(nullable=True, index=True)
    shipping_fee: str = Field(nullable=True, index=True)
    c_gst: int = Field(nullable=True, index=True)
    s_gst: int = Field(nullable=True, index=True)
    sub_total: int = Field(nullable=True, index=True)
    total_amount: int = Field(nullable=True, index=True)
    shipping_address: int = Field(
        foreign_key="user_shipping_address.id", nullable=False
    )
    paid_amount: int = Field(nullable=True, index=True)
    invoice: str = Field(nullable=True, index=True)


class Payment_details(ItemBase, table=True):
    __tablename__ = (
        "payment_details"  # Optional, automatically inferred from the class name
    )
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    payment_id: str = Field(nullable=True, index=True)
    payment_amount: int = Field(nullable=True, index=True)
    payment_status: str = Field(nullable=True, index=True)
    payment_response: Optional[dict] = Field(sa_column=Column(JSON))
