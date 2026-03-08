from typing import Optional
from pydantic import BaseModel


class BanBody(BaseModel):
    banned: Optional[bool] = True


class VerifySupplierBody(BaseModel):
    verified: Optional[bool] = True
