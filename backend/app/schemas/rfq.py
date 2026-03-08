from typing import Optional, Literal
from pydantic import BaseModel, Field


class RfqItem(BaseModel):
    productId: str
    quantity: int = Field(..., ge=1)
    notes: Optional[str] = None


class RfqCreate(BaseModel):
    items: Optional[list[RfqItem]] = None
    fromCart: Optional[bool] = None


class RfqStatusUpdate(BaseModel):
    status: Literal["closed", "rejected"]


class QuoteItemSubmit(BaseModel):
    productId: str
    unitPrice: float = Field(..., ge=0)
    availableQty: int = Field(..., ge=0)
    deliveryDays: Optional[int] = Field(None, ge=0)


class QuoteSubmit(BaseModel):
    items: Optional[list[QuoteItemSubmit]] = None
    message: Optional[str] = None
