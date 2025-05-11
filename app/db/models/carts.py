from datetime import datetime
from enum import IntEnum
from typing import Optional
from sqlmodel import Field, SQLModel

class ItemBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Carts(ItemBase, table=True):  # Use table=True to indicate this is a table
    __tablename__ = "carts"  # Optional, automatically inferred from the class name
    product_id: int=Field(foreign_key="products.id", nullable=False)
    session_id: str = Field(nullable=False, index=True)
    certificate_color: str = Field(nullable=True, index=True)
    frame_color: str = Field(nullable=True, index=True)
    frame_size: str = Field(nullable=True, index=True)
    frame_thickness: str = Field(nullable=True, index=True)
