from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from app.models.transaction import Transaction
from app.models.user import User
from app.models.fraud_alert import UserStats
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionList
from app.core.logging_config import get_logger

logger = get_logger("transactions")


class TransactionService:
    """Service for managing transactions"""

    def __init__(self, db: Session):
        self.db = db

    async def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction and update user statistics

        Args:
            transaction_data (TransactionCreate): Transaction data including user_id, amount, type, location, and device_info

        Returns:
            Transaction: The created transaction

        Raises:
            ValueError: If user is not found, is inactive, or has insufficient balance
        """
        logger.info(f"Creating transaction for user {transaction_data.user_id}")

        user = self.db.query(User).filter(User.user_id == transaction_data.user_id).first()
        if not user:
            logger.error(
                f"Transaction creation failed - User not found: {transaction_data.user_id}"
            )
            raise ValueError("Usuário não encontrado")

        if not user.is_active:
            logger.warning(
                f"Transaction creation failed - Inactive user: {transaction_data.user_id}"
            )
            raise ValueError("Usuário inativo")

        if transaction_data.type in ['withdraw', 'payment', 'transfer']:
            if user.balance < transaction_data.amount:
                logger.warning(
                    f"Transaction creation failed - Insufficient balance: User {transaction_data.user_id}, "
                    f"Balance: {user.balance}, Required: {transaction_data.amount}"
                )
                raise ValueError(f"Saldo insuficiente. Saldo atual: R$ {user.balance}")

        logger.debug(
            f"Creating transaction: amount={transaction_data.amount}, type={transaction_data.type}, "
            f"location=({transaction_data.latitude}, {transaction_data.longitude})"
        )

        db_transaction = Transaction(
            user_id=transaction_data.user_id,
            amount=transaction_data.amount,
            type=transaction_data.type,
            latitude=transaction_data.latitude,
            longitude=transaction_data.longitude,
            device_info=transaction_data.device_info,
        )

        try:
            self.db.add(db_transaction)
            
            if db_transaction.status == 'completed':
                if transaction_data.type == 'deposit':
                    user.balance += transaction_data.amount
                    logger.debug(f"User balance increased: {user.balance}")
                elif transaction_data.type in ['withdraw', 'payment', 'transfer']:
                    user.balance -= transaction_data.amount
                    logger.debug(f"User balance decreased: {user.balance}")
            
            self.db.commit()
            self.db.refresh(db_transaction)
            self.db.refresh(user)

            logger.info(
                f"Transaction created successfully - ID: {db_transaction.transaction_id}, "
                f"User: {transaction_data.user_id}, Amount: {transaction_data.amount}, "
                f"New Balance: {user.balance}"
            )

            await self._update_user_stats(transaction_data.user_id, transaction_data.amount)
        except Exception as e:
            logger.error(
                f"Failed to create transaction for user {transaction_data.user_id}: {str(e)}"
            )
            self.db.rollback()
            raise

        return db_transaction

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get a specific transaction by ID

        Args:
            transaction_id (int): ID of the transaction to retrieve

        Returns:
            Optional[Transaction]: The transaction if found, None otherwise
        """
        logger.debug(f"Fetching transaction with ID: {transaction_id}")

        transaction = (
            self.db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        )

        if transaction:
            logger.debug(f"Transaction found: {transaction_id}")
        else:
            logger.warning(f"Transaction not found: {transaction_id}")

        return transaction

    def list_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> TransactionList:
        """List transactions with optional filtering

        Args:
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 50.
            user_id (Optional[int], optional): ID of the user to filter transactions by. Defaults to None.
            status (Optional[str], optional): Transaction status to filter by. Defaults to None.

        Returns:
            TransactionList: List of transactions with pagination information
        """
        logger.info(
            f"Listing transactions - skip: {skip}, limit: {limit}, user_id: {user_id}, status: {status}"
        )

        query = self.db.query(Transaction)

        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if status:
            query = query.filter(Transaction.status == status)

        total = query.count()
        transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

        logger.info(f"Retrieved {len(transactions)} transactions out of {total} total")

        return TransactionList(
            transactions=transactions, total=total, page=skip // limit + 1, per_page=limit
        )

    def get_user_transactions(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> List[Transaction]:
        """Get transactions for a specific user

        Args:
            user_id (int): ID of the user
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 50.

        Returns:
            List[Transaction]: List of transactions for the user
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_transaction(
        self, transaction_id: int, transaction_update: TransactionUpdate
    ) -> Optional[Transaction]:
        """Update an existing transaction

        Args:
            transaction_id (int): ID of the transaction to update
            transaction_update (TransactionUpdate): Updated transaction data

        Returns:
            Optional[Transaction]: The updated transaction if found, None otherwise
        """
        logger.info(f"Updating transaction {transaction_id}")

        transaction = self.get_transaction(transaction_id)
        if not transaction:
            logger.warning(f"Transaction update failed - Transaction not found: {transaction_id}")
            return None

        update_data = transaction_update.dict(exclude_unset=True)
        logger.debug(f"Updating transaction {transaction_id} with data: {update_data}")

        for field, value in update_data.items():
            setattr(transaction, field, value)

        try:
            self.db.commit()
            self.db.refresh(transaction)
            logger.info(f"Transaction {transaction_id} updated successfully")
            return transaction
        except Exception as e:
            logger.error(f"Failed to update transaction {transaction_id}: {str(e)}")
            self.db.rollback()
            raise

    async def _update_user_stats(self, user_id: int, new_amount: Decimal):
        """Update user transaction statistics

        Args:
            user_id (int): ID of the user
            new_amount (Decimal): Amount of the new transaction

        Note:
            This is a private method that updates the user's average transaction amount,
            standard deviation, transaction count, and last transaction date
        """
        logger.debug(f"Updating user statistics for user {user_id}")

        stats = self.db.query(UserStats).filter(UserStats.user_id == user_id).first()

        if not stats:
            logger.info(f"Creating new user stats for user {user_id}")
            stats = UserStats(user_id=user_id)
            self.db.add(stats)

        if stats.transaction_count == 0:
            stats.avg_transaction_amount = new_amount
            stats.std_transaction_amount = Decimal("0")
            stats.transaction_count = 1
            logger.debug(f"First transaction for user {user_id} - amount: {new_amount}")
        else:
            old_avg = stats.avg_transaction_amount or Decimal("0")
            stats.transaction_count += 1
            stats.avg_transaction_amount = (
                old_avg * (stats.transaction_count - 1) + new_amount
            ) / stats.transaction_count

            # Calculate standard deviation using SQL for better performance
            std_result = (
                self.db.query(func.stddev(Transaction.amount))
                .filter(Transaction.user_id == user_id)
                .scalar()
            )

            stats.std_transaction_amount = Decimal(str(std_result)) if std_result else Decimal("0")

            logger.debug(
                f"Updated user {user_id} stats - count: {stats.transaction_count}, avg: {stats.avg_transaction_amount}, std: {stats.std_transaction_amount}"
            )

        stats.last_transaction_date = datetime.now(timezone.utc)
        stats.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()
            logger.debug(f"User stats updated successfully for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to update user stats for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
