from typing import Optional, Literal
from datetime import datetime
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
    unitPrice: float = Field(..., gt=0)
    availableQty: int = Field(..., gt=0)
    deliveryDays: int = Field(..., gt=0)
    itemNote: Optional[str] = Field(None, max_length=2000)


class QuoteSubmit(BaseModel):
    """POST /api/rfq/{id}/quote — items must cover every RFQ line for this seller's products."""

    items: list[QuoteItemSubmit] = Field(..., min_length=1)
    message: Optional[str] = Field(None, max_length=5000)
    termsAndConditions: Optional[str] = Field(None, max_length=10000)
    quoteValidUntil: datetime
