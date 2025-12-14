from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TransactionType(str, Enum):
    deposit = "deposit"
    withdraw = "withdraw"
    transfer = "transfer"
    payment = "payment"


class TransactionStatus(str, Enum):
    completed = "completed"
    failed = "failed"


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Valor da transação deve ser positivo")
    type: TransactionType
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Longitude (-180 to 180)")
    device_info: Optional[str] = None
    
    @field_validator('longitude')
    @classmethod
    def validate_coordinates_together(cls, v, info):
        latitude = info.data.get('latitude')
        if (latitude is None) != (v is None):
            raise ValueError("Both latitude and longitude must be provided together or both omitted")
        return v


class TransactionCreate(TransactionBase):
    user_id: int


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    is_flagged: Optional[bool] = None
    is_analyzed: Optional[bool] = None


class TransactionResponse(TransactionBase):
    transaction_id: int
    user_id: int
    status: TransactionStatus
    created_at: datetime
    is_flagged: bool
    is_analyzed: bool
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionList(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    page: int
    per_page: int
