from typing import Literal
from pydantic import BaseModel


class OrderStatusUpdate(BaseModel):
    status: Literal["confirmed", "processing", "shipped", "delivered", "cancelled"]
