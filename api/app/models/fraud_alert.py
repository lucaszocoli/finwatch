from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    alert_id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reason = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="fraud_alerts")
    user = relationship("User", back_populates="fraud_alerts")


class UserStats(Base):
    __tablename__ = "user_stats"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    avg_transaction_amount = Column(DECIMAL(12, 2))
    std_transaction_amount = Column(DECIMAL(12, 2))
    transaction_count = Column(Integer, default=0)
    last_transaction_date = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_stats")
