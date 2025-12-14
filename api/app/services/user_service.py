from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from app.models.user import User
from app.models.fraud_alert import UserStats
from app.schemas.user import UserCreate, UserUpdate, UserWithTransactions
from app.core.logging_config import get_logger
from app.services.geocoding_service import GeocodingService
from app.core.redis_client import get_redis

import random

logger = get_logger("users")


class UserService:
    """Service for managing users"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with initial statistics

        Args:
            user_data (UserCreate): User data including name and email

        Returns:
            User: The created user

        Raises:
            ValueError: If email is already in use
        """
        logger.info(f"Creating new user with email: {user_data.email}")

        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"User creation failed - Email already in use: {user_data.email}")
            raise ValueError("Email já está em uso")

        try:
            initial_balance = user_data.initial_balance
            if initial_balance is None:
                initial_balance = Decimal(random.uniform(1000, 50000)).quantize(Decimal('0.01'))
            
            latitude = None
            longitude = None
            
            if user_data.city:
                try:
                    redis_client = get_redis()
                    geocoding_service = GeocodingService(redis_client)
                    latitude, longitude = geocoding_service.geocode_address(
                        city=user_data.city,
                        state=user_data.state,
                        country=user_data.country or "Brazil"
                    )
                    
                    if latitude and longitude:
                        logger.info(
                            f"Geocoded {user_data.city}, {user_data.state}: "
                            f"({latitude}, {longitude})"
                        )
                except Exception as e:
                    logger.warning(f"Geocoding failed for user {user_data.email}: {e}")
            
            db_user = User(
                name=user_data.name,
                email=user_data.email,
                city=user_data.city,
                state=user_data.state,
                country=user_data.country or "Brazil",
                latitude=latitude,
                longitude=longitude,
                initial_balance=initial_balance,
                balance=initial_balance
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            logger.info(
                f"User created successfully - ID: {db_user.user_id}, "
                f"Email: {user_data.email}, Initial Balance: {initial_balance}, "
                f"Location: {user_data.city}, {user_data.state}"
            )

            user_stats = UserStats(user_id=db_user.user_id)
            self.db.add(user_stats)
            self.db.commit()

            logger.debug(f"User stats initialized for user {db_user.user_id}")

            return db_user
        except Exception as e:
            logger.error(f"Failed to create user with email {user_data.email}: {str(e)}")
            self.db.rollback()
            raise

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a specific user by ID

        Args:
            user_id (int): ID of the user to retrieve

        Returns:
            Optional[User]: The user if found, None otherwise
        """
        logger.debug(f"Fetching user with ID: {user_id}")

        user = self.db.query(User).filter(User.user_id == user_id).first()

        if user:
            logger.debug(f"User found: {user_id}")
        else:
            logger.warning(f"User not found: {user_id}")

        return user

    def get_user_with_stats(self, user_id: int) -> Optional[UserWithTransactions]:
        """Get a user with their transaction data

        Args:
            user_id (int): ID of the user to retrieve

        Returns:
            Optional[UserWithTransactions]: The user with transactions if found, None otherwise
        """
        user = (
            self.db.query(User)
            .options(joinedload(User.transactions))
            .filter(User.user_id == user_id)
            .first()
        )
        if not user:
            return None

        return UserWithTransactions.model_validate(user)

    def list_users(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[User]:
        """List users with optional filtering

        Args:
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 100.
            active_only (bool, optional): Whether to return only active users. Defaults to True.

        Returns:
            List[User]: List of users
        """
        logger.info(f"Listing users - skip: {skip}, limit: {limit}, active_only: {active_only}")

        query = self.db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)

        users = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(users)} users")

        return users

    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update an existing user

        Args:
            user_id (int): ID of the user to update
            user_update (UserUpdate): Updated user data

        Returns:
            Optional[User]: The updated user if found, None otherwise
        """
        logger.info(f"Updating user {user_id}")

        user = self.get_user(user_id)
        if not user:
            logger.warning(f"User update failed - User not found: {user_id}")
            return None

        update_data = user_update.dict(exclude_unset=True)
        logger.debug(f"Updating user {user_id} with data: {update_data}")

        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"User {user_id} updated successfully")
            return user
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            self.db.rollback()
            raise

    def delete_user(self, user_id: int) -> bool:
        """Soft delete a user by setting is_active to False

        Args:
            user_id (int): ID of the user to delete

        Returns:
            bool: True if user was found and deactivated, False if user not found
        """
        logger.info(f"Deleting user {user_id} (soft delete)")

        user = self.get_user(user_id)
        if not user:
            logger.warning(f"User deletion failed - User not found: {user_id}")
            return False

        try:
            user.is_active = False
            self.db.commit()
            logger.info(f"User {user_id} deactivated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            self.db.rollback()
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address

        Args:
            email (str): Email address of the user to retrieve

        Returns:
            Optional[User]: The user if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
