from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from .transaction import TransactionResponse


class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithTransactions(UserResponse):
    transactions: List[TransactionResponse] = []

    class Config:
        from_attributes = True
