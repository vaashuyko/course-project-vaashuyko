from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: int
    exp: int

class WishBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    link: Optional[str] = Field(None, max_length=500)
    price_estimate: Decimal = Field(
        ...,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    notes: Optional[str] = Field(None, max_length=1000)


class WishCreate(WishBase):
    pass

class WishUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    link: Optional[str] = Field(None, max_length=500)
    price_estimate: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    notes: Optional[str] = Field(None, max_length=1000)
    is_favorite: Optional[bool] = None

class WishRead(WishBase):
    id: int
    owner_id: int
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WishListResponse(BaseModel):
    items: list[WishRead]
    total: int
    limit: int
    offset: int
