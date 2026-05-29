"""
Credential management API endpoints — issue and list credentials.
"""



from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.credential import (
    CredentialCreate,
    CredentialListResponse,
    CredentialResponse,
)
from app.services.credential_service import (
    get_credential_detail,
    get_user_credentials,
    issue_credential,
)

router = APIRouter(prefix="/credentials", tags=["Credentials"])


@router.post(
    "/issue",
    response_model=CredentialResponse,
    status_code=201,
    summary="Issue a new credential",
    description="Create a cryptographically signed verifiable credential with Merkle tree and Ed25519 signature.",
)
async def issue(
    request: Request,
    data: CredentialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await issue_credential(db, current_user.id, data)


@router.get(
    "",
    response_model=CredentialListResponse,
    summary="List your credentials",
    description="Retrieve all credentials issued by the authenticated user.",
)
async def list_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    credentials = await get_user_credentials(db, current_user.id)
    return CredentialListResponse(credentials=credentials, total=len(credentials))


@router.get(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Get credential details",
    description="Retrieve a specific credential by ID (must be owner).",
)
async def get_credential(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    credential = await get_credential_detail(db, credential_id, current_user.id)
    return CredentialResponse.from_credential(credential)
