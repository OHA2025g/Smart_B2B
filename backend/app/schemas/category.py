from typing import Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    slug: Optional[str] = None
    icon: Optional[str] = None
    isActive: Optional[bool] = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    slug: Optional[str] = None
    icon: Optional[str] = None
    isActive: Optional[bool] = None
