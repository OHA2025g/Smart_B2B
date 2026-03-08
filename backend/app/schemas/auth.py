from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Literal["buyer", "seller"] = "buyer"
    name: str = Field(..., min_length=1)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
