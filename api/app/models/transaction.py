from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    type = Column(String(30), nullable=False)  # deposit, withdraw, transfer, payment
    status = Column(
        String(20), nullable=False, default="completed"
    )  # completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    location = Column(String(255), nullable=True)
    device_info = Column(String(255), nullable=True)
    is_flagged = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
    fraud_alerts = relationship("FraudAlert", back_populates="transaction")
