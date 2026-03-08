from typing import Optional
from pydantic import BaseModel


class QuoteItemUpdate(BaseModel):
    productId: str
    unitPrice: float
    availableQty: int
    deliveryDays: Optional[int] = None


class QuoteUpdate(BaseModel):
    items: Optional[list[QuoteItemUpdate]] = None
    message: Optional[str] = None
