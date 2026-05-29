"""
Selective disclosure sharing API endpoints — create, list, and revoke shares.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import limiter
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.share import ShareListResponse, ShareRequest, ShareResponse
from app.services.share_service import create_share, get_user_shares, revoke_share

router = APIRouter(prefix="/credentials", tags=["Selective Disclosure"])


@router.post(
    "/share",
    response_model=ShareResponse,
    status_code=201,
    summary="Create a selective disclosure share",
    description=(
        "Select specific fields from a credential to share. "
        "Generates Merkle proofs for each selected field and returns a "
        "time-limited share link + QR code data."
    ),
)
@limiter.limit("30/minute")
async def share_credential(
    request: Request,
    data: ShareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_share(db, current_user.id, data)


@router.get(
    "/shares",
    response_model=ShareListResponse,
    summary="List your active shares",
    description="Retrieve all shared presentations created by the authenticated user.",
)
async def list_shares(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_user_shares(db, current_user.id)


@router.delete(
    "/shares/{share_token}",
    status_code=204,
    summary="Revoke a share",
    description="Delete a shared presentation by its token (must be owner).",
)
async def delete_share(
    share_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await revoke_share(db, current_user.id, share_token)
