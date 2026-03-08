from typing import Optional
from pydantic import BaseModel, Field


class CartAdd(BaseModel):
    productId: str
    quantity: int = Field(1, ge=1)
    notes: Optional[str] = None
