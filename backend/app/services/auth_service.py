"""
Authentication service — handles user registration and login with JWT tokens.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.crud.user_crud import create_user, get_user_by_email
from app.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)


async def register_user(
    db: AsyncSession, data: UserRegister
) -> TokenResponse:
    """
    Register a new user account.
    
    Validates email uniqueness, hashes the password, creates the user,
    and returns JWT token pair.
    """
    # Check for existing user
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user
    hashed = hash_password(data.password)
    user = await create_user(db, data.email, data.full_name, hashed)

    # Generate tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def login_user(
    db: AsyncSession, data: UserLogin
) -> TokenResponse:
    """
    Authenticate a user and return JWT tokens.
    
    Verifies email exists and password matches the stored hash.
    """
    user = await get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )
