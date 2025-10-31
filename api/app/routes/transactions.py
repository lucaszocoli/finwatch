from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionList,
)
from app.services.transaction_service import TransactionService
from app.core.logging_config import get_logger

logger = get_logger("transactions")

router = APIRouter()


@router.post("/transactions/", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction: TransactionCreate, db: Session = Depends(get_db)
) -> TransactionResponse:
    """Create a new transaction.

    Args:
        transaction (TransactionCreate): The transaction to create.
        db (Session): Database session.

    Returns:
        TransactionResponse: The created transaction.
    """
    logger.info(f"POST /transactions/ - Creating transaction for user {transaction.user_id}")

    try:
        transaction_service = TransactionService(db)
        created_transaction = await transaction_service.create_transaction(transaction)
        logger.info(f"Transaction created successfully - ID: {created_transaction.transaction_id}")
        return created_transaction
    except ValueError as e:
        logger.warning(f"Transaction creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int, db: Session = Depends(get_db)
) -> TransactionResponse:
    """Get a specific transaction by ID.

    Args:
        transaction_id (int): The ID of the transaction to retrieve.
        db (Session): Database session.

    Returns:
        TransactionResponse: The requested transaction.
    """
    logger.info(f"GET /transactions/{transaction_id} - Fetching transaction")

    try:
        transaction_service = TransactionService(db)
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            raise HTTPException(status_code=404, detail="Transação não encontrada")

        logger.info(f"Transaction retrieved successfully: {transaction_id}")
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/", response_model=TransactionList)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
) -> TransactionList:
    """List transactions with optional filters.

    Args:
        skip (int, optional): Number of records to skip. Defaults to Query(0, ge=0).
        limit (int, optional): Maximum number of records to return. Defaults to Query(50, ge=1, le=100).
        user_id (int, optional): User ID to filter transactions. Defaults to Query(None).
        status (str, optional): Transaction status to filter transactions. Defaults to Query(None).
        db (Session): Database session.

    Returns:
        TransactionList: List of transactions.
    """
    logger.info(
        f"GET /transactions/ - Listing transactions with skip={skip}, limit={limit}, user_id={user_id}, status={status}"
    )

    try:
        transaction_service = TransactionService(db)
        result = transaction_service.list_transactions(
            skip=skip, limit=limit, user_id=user_id, status=status
        )
        logger.info(f"Retrieved {len(result.transactions)} transactions")
        return result
    except Exception as e:
        logger.error(f"Unexpected error listing transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}/transactions", response_model=List[TransactionResponse])
async def get_user_transactions(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    """Get transactions for a specific user.

    Args:
        user_id (int): The ID of the user to retrieve transactions for.
        skip (int, optional): Number of records to skip. Defaults to Query(0, ge=0).
        limit (int, optional): Maximum number of records to return. Defaults to Query(50, ge=1, le=100).
        db (Session): Database session.

    Returns:
        List[TransactionResponse]: List of transactions for the user.
    """
    logger.info(f"GET /users/{user_id}/transactions - Fetching transactions for user")

    try:
        transaction_service = TransactionService(db)
        transactions = transaction_service.get_user_transactions(user_id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
        return transactions
    except Exception as e:
        logger.error(f"Unexpected error retrieving transactions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int, transaction_update: TransactionUpdate, db: Session = Depends(get_db)
) -> TransactionResponse:
    """Update a specific transaction.

    Args:
        transaction_id (int): The ID of the transaction to update.
        transaction_update (TransactionUpdate): The updated transaction data.
        db (Session): Database session.

    Returns:
        TransactionResponse: The updated transaction.
    """
    logger.info(f"PUT /transactions/{transaction_id} - Updating transaction")

    try:
        transaction_service = TransactionService(db)
        transaction = transaction_service.update_transaction(transaction_id, transaction_update)
        if not transaction:
            logger.warning(f"Transaction update failed - Transaction not found: {transaction_id}")
            raise HTTPException(status_code=404, detail="Transação não encontrada")

        logger.info(f"Transaction updated successfully: {transaction_id}")
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
