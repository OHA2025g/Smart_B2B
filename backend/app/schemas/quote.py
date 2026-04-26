from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class QuoteItemUpdate(BaseModel):
    productId: str
    unitPrice: float = Field(..., gt=0)
    availableQty: int = Field(..., gt=0)
    deliveryDays: int = Field(..., gt=0)
    itemNote: Optional[str] = Field(None, max_length=2000)


class QuoteUpdate(BaseModel):
    items: Optional[list[QuoteItemUpdate]] = None
    message: Optional[str] = Field(None, max_length=5000)
    commitment_note: Optional[str] = None
    deliveryCommitment: Optional[str] = Field(None, max_length=2000)
    warrantyOrSupportNote: Optional[str] = Field(None, max_length=2000)
    termsAndConditions: Optional[str] = Field(None, max_length=10000)
    quoteValidUntil: Optional[datetime] = None
