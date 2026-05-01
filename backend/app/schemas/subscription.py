from typing import Literal
from pydantic import BaseModel, Field


class SubscriptionCheckoutBody(BaseModel):
    plan: Literal["go", "pro"] = Field(..., description="Target paid plan")

class PaymentSimulateBody(BaseModel):
    result: Literal["success", "failed"] = "success"
    method: Literal["demo_card", "demo_upi", "demo_netbanking"] = "demo_card"

class OrderPaymentSimulateBody(PaymentSimulateBody):
    pass
