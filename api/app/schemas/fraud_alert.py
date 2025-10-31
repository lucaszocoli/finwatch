from datetime import datetime
from pydantic import BaseModel, Field


class FraudAlertBase(BaseModel):
    reason: str
    score: float = Field(..., ge=0.0, le=1.0, description="Score must be between 0 and 1")


class FraudAlertCreate(FraudAlertBase):
    transaction_id: int
    user_id: int


class FraudAlertResponse(FraudAlertBase):
    alert_id: int
    transaction_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FraudAlertList(BaseModel):
    alerts: list[FraudAlertResponse]
    total: int
    high_risk_count: int


class FraudStats(BaseModel):
    total_alerts: int
    avg_score: float
    alerts_last_24h: int
    top_reasons: list[dict[str, int]]
