from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserWithTransactions
from app.services.user_service import UserService
from app.core.logging_config import get_logger

logger = get_logger("users")

router = APIRouter()


@router.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """Create a new user.

    Args:
        user (UserCreate): The user to create.
        db (Session): Database session.

    Returns:
        UserResponse: The created user.
    """
    logger.info(f"POST /users/ - Creating user with email: {user.email}")

    try:
        user_service = UserService(db)
        created_user = user_service.create_user(user)
        logger.info(f"User created successfully - ID: {created_user.user_id}")
        return created_user
    except ValueError as e:
        logger.warning(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{user_id}", response_model=UserWithTransactions)
async def get_user(user_id: int, db: Session = Depends(get_db)) -> UserWithTransactions:
    """Get a specific user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (Session): Database session.

    Returns:
        UserWithTransactions: The user with their transactions.
    """
    logger.info(f"GET /users/{user_id} - Fetching user")

    try:
        user_service = UserService(db)
        user = user_service.get_user_with_stats(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"User retrieved successfully: {user_id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """List users with optional filters.

    Args:
        skip (int, optional): Number of records to skip. Defaults to Query(0, ge=0).
        limit (int, optional): Maximum number of records to return. Defaults to Query(100, ge=1, le=100).
        active_only (bool, optional): Whether to filter for active users only. Defaults to Query(True).
        db (Session): Database session.

    Returns:
        List[UserResponse]: List of users.
    """
    logger.info(
        f"GET /users/ - Listing users with skip={skip}, limit={limit}, active_only={active_only}"
    )

    try:
        user_service = UserService(db)
        users = user_service.list_users(skip=skip, limit=limit, active_only=active_only)
        logger.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Unexpected error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)
) -> UserResponse:
    """Update a specific user.

    Args:
        user_id (int): ID of the user to update
        user_update (UserUpdate): user data to update.
        db (Session): Database session.

    Raises:
        HTTPException: If the user is not found.

    Returns:
        UserResponse: The updated user.
    """
    logger.info(f"PUT /users/{user_id} - Updating user")

    try:
        user_service = UserService(db)
        user = user_service.update_user(user_id, user_update)
        if not user:
            logger.warning(f"User update failed - User not found: {user_id}")
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        logger.info(f"User updated successfully: {user_id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a specific user.

    Args:
        user_id (int): ID of the user to delete.
        db (Session): Database session.

    Raises:
        HTTPException: If the user is not found.

    Returns:
        None
    """
    logger.info(f"DELETE /users/{user_id} - Deleting user")

    try:
        user_service = UserService(db)
        success = user_service.delete_user(user_id)
        if not success:
            logger.warning(f"User deletion failed - User not found: {user_id}")
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        logger.info(f"User deleted successfully: {user_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
