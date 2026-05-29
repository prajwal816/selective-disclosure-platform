"""
Credential service — handles credential issuance with Merkle tree construction
and Ed25519 signing.
"""

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import (
    MerkleTree,
    create_signing_payload,
    generate_salts_for_claims,
    get_signer,
)
from app.crud.credential_crud import (
    create_credential,
    get_credential_by_id,
    get_credentials_by_user_id,
)
from app.models.credential import Credential
from app.schemas.credential import CredentialCreate, CredentialResponse

settings = get_settings()


async def issue_credential(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: CredentialCreate,
) -> CredentialResponse:
    """
    Issue a new cryptographically signed credential.
    
    Process:
    1. Generate random salt for each claim
    2. Build Merkle tree from salted claim leaves
    3. Sign Merkle root + issuer metadata with Ed25519
    4. Store everything in the database
    """
    signer = get_signer()

    # Step 1: Generate per-claim salts
    salts = generate_salts_for_claims(data.claims)

    # Step 2: Build Merkle tree
    tree_data = MerkleTree.build(data.claims, salts)

    # Step 3: Create signing payload and sign
    issued_at = datetime.now(timezone.utc).isoformat()
    signing_payload = create_signing_payload(
        tree_data.root, settings.ISSUER_DID, issued_at
    )
    signature = signer.sign(signing_payload)

    # Step 4: Serialize tree data for storage
    tree_data_dict = {
        "root": tree_data.root,
        "leaves": tree_data.leaves,
        "leaf_keys": tree_data.leaf_keys,
        "tree_levels": tree_data.tree_levels,
    }

    # Step 5: Store credential
    credential = await create_credential(
        db=db,
        user_id=user_id,
        credential_type=data.credential_type,
        claims=data.claims,
        salts=salts,
        merkle_root=tree_data.root,
        signature=signature,
        issuer_did=settings.ISSUER_DID,
        public_key_hex=signer.public_key_hex,
        tree_data=tree_data_dict,
    )

    return CredentialResponse.from_credential(credential)


async def get_user_credentials(
    db: AsyncSession, user_id: uuid.UUID
) -> List[CredentialResponse]:
    """Fetch all credentials belonging to a user."""
    credentials = await get_credentials_by_user_id(db, user_id)
    return [CredentialResponse.from_credential(c) for c in credentials]


async def get_credential_detail(
    db: AsyncSession, credential_id: uuid.UUID, user_id: uuid.UUID
) -> Credential:
    """
    Fetch a single credential with ownership verification.
    Returns the full ORM model (including salts and tree data).
    """
    credential = await get_credential_by_id(db, credential_id)

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

    return credential
