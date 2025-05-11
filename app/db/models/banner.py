from datetime import datetime
from enum import IntEnum
from typing import Optional
from sqlmodel import Field, SQLModel

class ItemBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Banners(ItemBase,table=True):
    __tablename__ = "banners"
    banner_name: str = Field(nullable=True, index=True)
    banner_priority: int = Field(nullable=True, index=True, max_length=100)