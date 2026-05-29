"""
Public verification API endpoints — verify shared presentations (no auth required).
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import limiter
from app.database import get_db
from app.schemas.verify import PresentationData, VerificationResult
from app.services.verify_service import get_presentation, verify_presentation_by_token

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get(
    "/{share_token}",
    response_model=PresentationData,
    summary="Get shared presentation",
    description=(
        "Fetch a shared presentation by its token. Returns disclosed fields "
        "and automatic cryptographic verification results. No authentication required."
    ),
)
@limiter.limit("20/minute")
async def get_shared_presentation(
    request: Request,
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    return await get_presentation(db, share_token)


@router.post(
    "",
    response_model=VerificationResult,
    summary="Verify a presentation",
    description=(
        "Perform full cryptographic verification of a shared presentation. "
        "Verifies Merkle proofs and Ed25519 signature. No authentication required."
    ),
)
@limiter.limit("20/minute")
async def verify_presentation(
    request: Request,
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    return await verify_presentation_by_token(db, share_token)
