from typing import Optional
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    unit: Optional[str] = "unit"
    minOrderQuantity: Optional[int] = Field(1, ge=0)
    city: Optional[str] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    minOrderQuantity: Optional[int] = Field(None, ge=0)
    city: Optional[str] = None
    isActive: Optional[bool] = None
