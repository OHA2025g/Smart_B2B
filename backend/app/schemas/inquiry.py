from pydantic import BaseModel, Field


class InquiryCreate(BaseModel):
    productId: str
    message: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
