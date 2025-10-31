from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.fraud_alert import FraudAlert
from app.schemas.fraud_alert import FraudAlertList, FraudStats
from app.core.logging_config import get_logger

logger = get_logger("fraud")


class FraudAlertService:
    """Service for managing fraud alerts"""

    def __init__(self, db: Session):
        self.db = db

    def get_alert(self, alert_id: int) -> Optional[FraudAlert]:
        """Get a specific fraud alert by ID

        Args:
            alert_id (int): ID of the fraud alert to retrieve

        Returns:
            Optional[FraudAlert]: The fraud alert if found, None otherwise
        """
        logger.debug(f"Fetching fraud alert with ID: {alert_id}")

        alert = self.db.query(FraudAlert).filter(FraudAlert.alert_id == alert_id).first()

        if alert:
            logger.debug(f"Fraud alert found: {alert_id}")
            if alert.score > 0.8:
                logger.warning(f"High-risk fraud alert accessed: {alert_id} - Score: {alert.score}")
        else:
            logger.warning(f"Fraud alert not found: {alert_id}")

        return alert

    def list_alerts(
        self, skip: int = 0, limit: int = 50, min_score: float = 0.0, user_id: Optional[int] = None
    ) -> FraudAlertList:
        """List fraud alerts

        Args:
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 50.
            min_score (float, optional): Minimum value of score to display. Defaults to 0.0.
            user_id (Optional[int], optional): ID of the user to filter alerts by. Defaults to None.

        Returns:
            FraudAlertList: List of fraud alerts.
        """
        logger.info(
            f"Listing fraud alerts - skip: {skip}, limit: {limit}, min_score: {min_score}, user_id: {user_id}"
        )

        query = self.db.query(FraudAlert).filter(FraudAlert.score >= min_score)

        if user_id:
            query = query.filter(FraudAlert.user_id == user_id)

        total = query.count()
        high_risk_count = query.filter(FraudAlert.score > 0.8).count()

        alerts = query.order_by(FraudAlert.created_at.desc()).offset(skip).limit(limit).all()

        logger.info(
            f"Retrieved {len(alerts)} fraud alerts out of {total} total ({high_risk_count} high-risk)"
        )

        if high_risk_count > 0:
            logger.warning(
                f"High-risk fraud alerts detected: {high_risk_count} alerts with score > 0.8"
            )

        return FraudAlertList(alerts=alerts, total=total, high_risk_count=high_risk_count)

    def get_user_alerts(self, user_id: int, skip: int = 0, limit: int = 20) -> List[FraudAlert]:
        """Retrieve alerts for a specific user

        Args:
            user_id (int): ID of the user
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 20.

        Returns:
            List[FraudAlert]: List of fraud alerts for the user
        """
        logger.info(f"Fetching fraud alerts for user {user_id}")

        alerts = (
            self.db.query(FraudAlert)
            .filter(FraudAlert.user_id == user_id)
            .order_by(FraudAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.info(f"Retrieved {len(alerts)} fraud alerts for user {user_id}")

        high_risk_alerts = [alert for alert in alerts if alert.score > 0.8]
        if high_risk_alerts:
            logger.warning(f"User {user_id} has {len(high_risk_alerts)} high-risk fraud alerts")

        return alerts

    def get_fraud_stats(self, days: int = 7) -> FraudStats:
        """Get fraud alert statistics for a specified time period

        Args:
            days (int, optional): Number of days to look back for statistics. Defaults to 7.

        Returns:
            FraudStats: Statistics including total alerts, average score, alerts in last 24h, and top reasons
        """
        logger.info(f"Generating fraud statistics for the last {days} days")

        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        alerts_query = self.db.query(FraudAlert).filter(FraudAlert.created_at >= since_date)

        total_alerts = alerts_query.count()

        avg_score_result = alerts_query.with_entities(func.avg(FraudAlert.score)).scalar()
        avg_score = float(avg_score_result) if avg_score_result else 0.0

        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        alerts_24h = alerts_query.filter(FraudAlert.created_at >= last_24h).count()

        top_reasons_query = (
            self.db.query(FraudAlert.reason, func.count(FraudAlert.reason).label("count"))
            .filter(FraudAlert.created_at >= since_date)
            .group_by(FraudAlert.reason)
            .order_by(func.count(FraudAlert.reason).desc())
            .limit(5)
            .all()
        )

        top_reasons = [{"reason": reason, "count": count} for reason, count in top_reasons_query]

        logger.info(
            f"Fraud stats generated - Total: {total_alerts}, Avg Score: {avg_score:.3f}, Last 24h: {alerts_24h}"
        )

        if avg_score > 0.7:
            logger.warning(f"High average fraud score detected: {avg_score:.3f} over {days} days")

        return FraudStats(
            total_alerts=total_alerts,
            avg_score=avg_score,
            alerts_last_24h=alerts_24h,
            top_reasons=top_reasons,
        )

    def create_alert(
        self, transaction_id: int, user_id: int, reason: str, score: float
    ) -> FraudAlert:
        """Create a new fraud alert

        Args:
            transaction_id (int): ID of the transaction that triggered the alert
            user_id (int): ID of the user associated with the transaction
            reason (str): Reason for the fraud alert
            score (float): Fraud score (0.0 to 1.0)

        Returns:
            FraudAlert: The created fraud alert
        """
        logger.warning(
            f"Creating fraud alert for transaction {transaction_id}, user {user_id} - Score: {score}, Reason: {reason}"
        )

        alert = FraudAlert(
            transaction_id=transaction_id, user_id=user_id, reason=reason, score=score
        )

        try:
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)

            logger.info(f"Fraud alert created successfully - ID: {alert.alert_id}")

            # Log high-risk alerts
            if score > 0.8:
                logger.error(
                    f"HIGH-RISK FRAUD ALERT: Alert ID {alert.alert_id}, Transaction {transaction_id}, User {user_id}, Score: {score}, Reason: {reason}"
                )
            elif score > 0.6:
                logger.warning(
                    f"MEDIUM-RISK FRAUD ALERT: Alert ID {alert.alert_id}, Transaction {transaction_id}, User {user_id}, Score: {score}, Reason: {reason}"
                )

            return alert
        except Exception as e:
            logger.error(f"Failed to create fraud alert for transaction {transaction_id}: {str(e)}")
            self.db.rollback()
            raise
