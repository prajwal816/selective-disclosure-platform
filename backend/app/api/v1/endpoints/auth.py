"""
Authentication API endpoints — register and login.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import limiter
from app.database import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserRegister
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new account with email, name, and password. Returns JWT tokens.",
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    return await register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with credentials",
    description="Authenticate with email and password. Returns JWT access and refresh tokens.",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    return await login_user(db, data)
