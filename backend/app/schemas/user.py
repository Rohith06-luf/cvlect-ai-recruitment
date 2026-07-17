from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: str = Field(default="Candidate")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserOut(UserBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    success: bool
    message: str
    data: UserOut | None = None
