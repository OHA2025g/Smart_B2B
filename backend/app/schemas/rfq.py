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
    deliveryLocation: str | None = Field(
        default=None, description="Required: where goods should be delivered."
    )
    requiredByDate: datetime | None = None
    buyerNotes: str | None = Field(default=None, max_length=10000)
    priority: Literal["normal", "urgent"] = "normal"
    validUntil: datetime | None = None


class RfqStatusUpdate(BaseModel):
    status: Literal["closed", "rejected"]


class QuoteItemSubmit(BaseModel):
    productId: str
    unitPrice: float = Field(..., gt=0)
    availableQty: int = Field(..., gt=0)
    deliveryDays: int = Field(..., gt=0)
    itemNote: str | None = Field(None, max_length=2000)



class BuyerCounterOfferCreate(BaseModel):
    """Buyer counter-offer; seller can reply with Revise quote."""

    quoteId: str
    message: str = Field(..., min_length=1, max_length=5000)
    proposedTotal: float | None = Field(None, ge=0, description="Optional target total the buyer is asking for (INR).")


class QuoteSubmit(BaseModel):
    """POST /api/rfq/{id}/quote - items must cover every RFQ line for this seller's products."""

    items: list[QuoteItemSubmit] = Field(..., min_length=1)
    message: str | None = Field(None, max_length=5000)
    termsAndConditions: str | None = Field(None, max_length=10000)
    quoteValidUntil: datetime
    deliveryCommitment: str | None = Field(None, max_length=2000)
    warrantyOrSupportNote: str | None = Field(None, max_length=2000)
