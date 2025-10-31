from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.fraud_alert import FraudAlertResponse, FraudAlertList, FraudStats
from app.services.fraud_alert_service import FraudAlertService
from app.core.logging_config import get_logger

logger = get_logger("fraud")

router = APIRouter()


@router.get("/fraud-alerts/", response_model=FraudAlertList)
async def list_fraud_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    user_id: int = Query(None),
    db: Session = Depends(get_db),
) -> FraudAlertList:
    """List fraud alerts with optional filters.

    Args:
        skip (int, optional): Number of records to skip. Defaults to Query(0, ge=0).
        limit (int, optional): Maximum number of records to return. Defaults to Query(50, ge=1, le=100).
        min_score (float, optional): Minimum fraud score to filter alerts. Defaults to Query(0.0, ge=0.0, le=1.0).
        user_id (int, optional): User ID to filter alerts. Defaults to Query(None).
        db (Session): Database session.

    Returns:
        FraudAlertList: List of fraud alerts.
    """
    logger.info(
        f"GET /fraud-alerts/ - Listing fraud alerts with skip={skip}, limit={limit}, min_score={min_score}, user_id={user_id}"
    )

    try:
        fraud_service = FraudAlertService(db)
        result = fraud_service.list_alerts(
            skip=skip, limit=limit, min_score=min_score, user_id=user_id
        )
        logger.info(f"Retrieved {len(result.alerts)} fraud alerts")
        return result
    except Exception as e:
        logger.error(f"Unexpected error listing fraud alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fraud-alerts/{alert_id}", response_model=FraudAlertResponse)
async def get_fraud_alert(alert_id: int, db: Session = Depends(get_db)) -> FraudAlertResponse:
    """Get a specific fraud alert by ID.

    Args:
        alert_id (int): The ID of the fraud alert to retrieve.
        db (Session): Database session.

    Raises:
        HTTPException: If the fraud alert is not found.

    Returns:
        FraudAlertResponse: The requested fraud alert.
    """
    logger.info(f"GET /fraud-alerts/{alert_id} - Fetching fraud alert")

    try:
        fraud_service = FraudAlertService(db)
        alert = fraud_service.get_alert(alert_id)
        if not alert:
            logger.warning(f"Fraud alert not found: {alert_id}")
            raise HTTPException(status_code=404, detail="Alerta não encontrado")

        logger.info(f"Fraud alert retrieved successfully: {alert_id}")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving fraud alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/fraud-alerts/stats/summary", response_model=FraudStats)
async def get_fraud_stats(
    days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db)
) -> FraudStats:
    """Get fraud statistics summary.

    Args:
        days (int, optional): Number of days to include in the summary. Defaults to Query(7, ge=1, le=365).
        db (Session): Database session.

    Returns:
        FraudStats: Summary of fraud statistics.
    """
    logger.info(f"GET /fraud-alerts/stats/summary - Generating fraud statistics for {days} days")

    try:
        fraud_service = FraudAlertService(db)
        stats = fraud_service.get_fraud_stats(days=days)
        logger.info(f"Fraud statistics generated successfully for {days} days")
        return stats
    except Exception as e:
        logger.error(f"Unexpected error generating fraud statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}/fraud-alerts", response_model=List[FraudAlertResponse])
async def get_user_fraud_alerts(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[FraudAlertResponse]:
    """Get fraud alerts for a specific user.

    Args:
        user_id (int): The ID of the user to retrieve fraud alerts for.
        skip (int, optional): Number of records to skip. Defaults to Query(0, ge=0).
        limit (int, optional): Maximum number of records to return. Defaults to Query(20, ge=1, le=100).
        db (Session): Database session.

    Returns:
        List[FraudAlertResponse]: List of fraud alerts for the user.
    """
    logger.info(f"GET /users/{user_id}/fraud-alerts - Fetching fraud alerts for user")

    try:
        fraud_service = FraudAlertService(db)
        alerts = fraud_service.get_user_alerts(user_id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(alerts)} fraud alerts for user {user_id}")
        return alerts
    except Exception as e:
        logger.error(f"Unexpected error retrieving fraud alerts for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
