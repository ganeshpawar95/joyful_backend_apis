from datetime import datetime
from enum import IntEnum
from typing import Optional
from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Banners(ItemBase, table=True):
    __tablename__ = "banners"
    banner_name: str = Field(nullable=True, index=True)
    banner_mobile: str = Field(nullable=True, index=True)

    banner_priority: int = Field(nullable=True, index=True)


class Category(ItemBase, table=True):
    __tablename__ = "categories"
    cat_img: str = Field(nullable=True, index=True)
    cat_mobile_img: str = Field(nullable=True, index=True)
    cat_name: str = Field(nullable=True, index=True)
    cat_priority: int = Field(nullable=True, index=True)
