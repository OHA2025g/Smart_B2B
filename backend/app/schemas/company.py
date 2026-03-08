from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class CompanyBody(BaseModel):
    companyName: str = Field(..., min_length=1)
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    phone: Optional[str] = None
    website: Optional[str] = None  # can be HttpUrl if strict
    gstNumber: Optional[str] = None
