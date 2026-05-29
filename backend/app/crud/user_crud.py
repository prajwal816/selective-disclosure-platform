"""
CRUD operations for the User model.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def create_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    hashed_password: str,
) -> User:
    """Create a new user record."""
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_email(
    db: AsyncSession, email: str
) -> Optional[User]:
    """Fetch a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession, user_id: str
) -> Optional[User]:
    """Fetch a user by their ID."""
    result = await db.execute(select(User).where(User.id == str(user_id)))
    return result.scalar_one_or_none()
