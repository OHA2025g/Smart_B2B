from typing import Literal
from pydantic import BaseModel


class OrderStatusUpdate(BaseModel):
    status: Literal["confirmed", "processing", "shipped", "delivered", "cancelled"]


class OrderPaymentUpdate(BaseModel):
    paymentStatus: Literal["payment_pending", "escrow_held", "released", "refunded"]
