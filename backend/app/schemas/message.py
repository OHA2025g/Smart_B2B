from typing import Optional

from pydantic import BaseModel, Field


class MessagePost(BaseModel):
    text: str = Field(..., min_length=1)
    confirm_send: Optional[bool] = False
