from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel, Field, Relationship

from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB


class ItemBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Certificate_colors(ItemBase, table=True):
    __tablename__ = "certificate_colors"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    name: str = Field(nullable=True, index=True)
    status: bool = Field(nullable=True, index=True)  # approved,pending,rejected
    priority: int = Field(nullable=True, index=True)

    # Define back relationship
    product: Optional["Products"] = Relationship(back_populates="certificate_colors")


class Frame_colors(ItemBase, table=True):
    __tablename__ = "frame_colors"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    name: str = Field(nullable=True, index=True)
    status: bool = Field(nullable=True, index=True)  # approved,pending,rejected
    priority: int = Field(nullable=True, index=True)
    # Define back relationship
    product: Optional["Products"] = Relationship(back_populates="frame_colors")


class Frame_size(ItemBase, table=True):
    __tablename__ = "frame_size"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    name: str = Field(nullable=True, index=True)
    status: bool = Field(nullable=True, index=True)  # approved,pending,rejected
    priority: int = Field(nullable=True, index=True)
    # Define back relationship
    product: Optional["Products"] = Relationship(back_populates="frame_size")


class Frame_Thickness(ItemBase, table=True):
    __tablename__ = "frame_thickness"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    name: str = Field(nullable=True, index=True)
    status: bool = Field(nullable=True, index=True)  # approved,pending,rejected
    priority: int = Field(nullable=True, index=True)
    # Define back relationship
    product: Optional["Products"] = Relationship(back_populates="frame_thickness")


class Product_images(ItemBase, table=True):
    __tablename__ = "product_images"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    images: str = Field(nullable=True, index=True)
    status: str = Field(nullable=True, index=True)  # approved,pending,rejected
    priority: int = Field(nullable=True, index=True)

    # Define back relationship
    product: Optional["Products"] = Relationship(back_populates="product_images")


class Product_Review_images(ItemBase, table=True):
    __tablename__ = "product_review_images"
    product_rating_id: int = Field(foreign_key="product_rating.id", nullable=False)
    images: str = Field(nullable=True, index=True)
    # Define back relationship
    product_rating: Optional["Product_rating"] = Relationship(
        back_populates="product_review_images"
    )


class Product_rating(ItemBase, table=True):
    __tablename__ = "product_rating"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    # user_id: int=Field(foreign_key="users.id", nullable=False)
    user_name: str = Field(nullable=True, index=True)
    title: str = Field(nullable=True, index=True)
    review: str = Field(nullable=True, index=True)
    rating: int = Field(nullable=True, index=True)
    status: str = Field(nullable=True, index=True)

    product: Optional["Products"] = Relationship(back_populates="product_ratings")
    product_review_images: List[Product_Review_images] = Relationship(
        back_populates="product_rating", sa_relationship_kwargs={"lazy": "joined"}
    )


class Product_tag_options(ItemBase, table=True):
    __tablename__ = "product_tag_options"
    product_id: int = Field(foreign_key="products.id", nullable=False)
    priority: int = Field(nullable=True, index=True)
    name: str = Field(nullable=True, index=True)
    tag: str = Field(nullable=True, index=True)
    tag_optional: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    product: Optional["Products"] = Relationship(back_populates="product_tag_options")


class Products(ItemBase, table=True):
    __tablename__ = "products"
    product_name: str = Field(nullable=True, index=True)
    url_name: str = Field(nullable=True, index=True)
    offer_price: str = Field(nullable=True, index=True)
    price: str = Field(nullable=True, index=True)
    thumbnail: str = Field(nullable=True, index=True)
    description: str = Field(nullable=True, index=True)
    care_instructions: str = Field(nullable=True, index=True)
    delivery_info: str = Field(nullable=True, index=True)
    meta_title: str = Field(nullable=True, index=True)
    meta_keywords: str = Field(nullable=True, index=True)
    meta_desc: str = Field(nullable=True, index=True)
    status: bool = Field(nullable=True, default=True, index=True)
    priority: int = Field(nullable=True, index=True)
    product_type: str = Field(nullable=True, index=True)
    product_trading_type: str = Field(nullable=True, index=True)

    is_digital: bool = Field(nullable=True, index=True)
    product_category: str = Field(nullable=True, index=True)

    # Define relationship correctly
    product_images: List[Product_images] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )

    product_ratings: List[Product_rating] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )

    product_tag_options: List[Product_tag_options] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )

    certificate_colors: List[Certificate_colors] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )
    frame_colors: List[Frame_colors] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )
    frame_size: List[Frame_size] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )
    frame_thickness: List[Frame_Thickness] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "joined"}
    )


class Product_shipping_rates(ItemBase, table=True):
    __tablename__ = "shipping_rates"
    start_price: str = Field(nullable=True, index=True)
    end_price: str = Field(nullable=True, index=True)
    shipping_rate: str = Field(nullable=True, index=True)
    status: str = Field(nullable=True, index=True)
