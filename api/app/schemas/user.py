from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from .transaction import TransactionResponse


class UserBase(BaseModel):
    name: str
    email: EmailStr
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "Brazil"
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    initial_balance: Optional[Decimal] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    user_id: int
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    initial_balance: Decimal
    balance: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithTransactions(UserResponse):
    transactions: List[TransactionResponse] = []

    class Config:
        from_attributes = True
