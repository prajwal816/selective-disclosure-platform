"""
Share service — handles selective disclosure presentation creation.

Generates Merkle proofs for selected fields and creates time-limited share links.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import MerkleTree, MerkleTreeData
from app.crud.credential_crud import get_credential_by_id, get_credentials_by_user_id
from app.crud.share_crud import (
    create_shared_presentation,
    delete_by_token,
    get_shares_by_user_credentials,
)
from app.schemas.share import ShareRequest, ShareResponse, ShareListItem, ShareListResponse

settings = get_settings()


async def create_share(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ShareRequest,
) -> ShareResponse:
    """
    Create a selective disclosure share for a credential.
    
    Process:
    1. Verify credential ownership
    2. Validate selected fields exist in the credential
    3. Reconstruct Merkle tree from stored data
    4. Generate Merkle proofs for each selected field
    5. Create share token with expiry
    6. Store the presentation and return share URL
    """
    # Step 1: Fetch and verify ownership
    credential = await get_credential_by_id(db, data.credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )
    if credential.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this credential",
        )

    # Step 2: Validate selected fields
    available_fields = set(credential.claims.keys())
    invalid_fields = set(data.selected_fields) - available_fields
    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fields: {', '.join(invalid_fields)}. "
                   f"Available: {', '.join(sorted(available_fields))}",
        )

    # Step 3: Reconstruct Merkle tree data from stored structure
    tree_data = MerkleTreeData(
        root=credential.tree_data["root"],
        leaves=credential.tree_data["leaves"],
        leaf_keys=credential.tree_data["leaf_keys"],
        tree_levels=credential.tree_data["tree_levels"],
    )

    # Step 4: Generate Merkle proofs for selected fields
    merkle_proofs = MerkleTree.generate_proofs_for_fields(
        selected_keys=data.selected_fields,
        claims=credential.claims,
        salts=credential.salts,
        tree_data=tree_data,
    )

    # Step 5: Generate share token and expiry
    share_token = secrets.token_urlsafe(48)
    expiry_hours = data.expiry_hours or settings.DEFAULT_SHARE_EXPIRY_HOURS
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    # Step 6: Store the presentation
    presentation = await create_shared_presentation(
        db=db,
        credential_id=credential.id,
        share_token=share_token,
        disclosed_fields=data.selected_fields,
        merkle_proofs=merkle_proofs,
        merkle_root=credential.merkle_root,
        signature=credential.signature,
        issuer_did=credential.issuer_did,
        public_key_hex=credential.public_key_hex,
        credential_type=credential.credential_type,
        credential_issued_at=credential.issued_at,
        expires_at=expires_at,
    )

    # Build response
    share_url = f"{settings.FRONTEND_URL}/verify/{share_token}"
    qr_data = share_url  # QR encodes the full URL

    return ShareResponse(
        share_token=share_token,
        share_url=share_url,
        qr_data=qr_data,
        expires_at=expires_at,
        disclosed_fields=data.selected_fields,
        total_original_fields=len(credential.claims),
    )


async def get_user_shares(
    db: AsyncSession, user_id: uuid.UUID
) -> ShareListResponse:
    """Fetch all shares created by the user."""
    credentials = await get_credentials_by_user_id(db, user_id)
    credential_ids = [c.id for c in credentials]

    shares = await get_shares_by_user_credentials(db, credential_ids)

    now = datetime.now(timezone.utc)
    items = []
    for s in shares:
        expires_at = s.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        items.append(
            ShareListItem(
                id=s.id,
                share_token=s.share_token,
                credential_id=s.credential_id,
                credential_type=s.credential_type,
                disclosed_fields=s.disclosed_fields,
                expires_at=expires_at,
                access_count=s.access_count,
                max_access_count=s.max_access_count,
                created_at=s.created_at,
                is_expired=now > expires_at,
            )
        )

    return ShareListResponse(shares=items, total=len(items))


async def revoke_share(
    db: AsyncSession, user_id: uuid.UUID, share_token: str
) -> bool:
    """Revoke (delete) a share, verifying ownership."""
    credentials = await get_credentials_by_user_id(db, user_id)
    credential_ids = [c.id for c in credentials]

    deleted = await delete_by_token(db, share_token, credential_ids)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or you don't have permission to revoke it",
        )
    return True
