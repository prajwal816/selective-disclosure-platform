"""
CRUD operations for the Credential model.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credential import Credential


async def create_credential(
    db: AsyncSession,
    user_id: uuid.UUID,
    credential_type: str,
    claims: dict,
    salts: dict,
    merkle_root: str,
    signature: str,
    issuer_did: str,
    public_key_hex: str,
    tree_data: dict,
) -> Credential:
    """Create a new credential with cryptographic metadata."""
    credential = Credential(
        user_id=user_id,
        credential_type=credential_type,
        claims=claims,
        salts=salts,
        merkle_root=merkle_root,
        signature=signature,
        issuer_did=issuer_did,
        public_key_hex=public_key_hex,
        tree_data=tree_data,
    )
    db.add(credential)
    await db.flush()
    await db.refresh(credential)
    return credential


async def get_credential_by_id(
    db: AsyncSession, credential_id: uuid.UUID
) -> Optional[Credential]:
    """Fetch a credential by its UUID."""
    result = await db.execute(
        select(Credential).where(Credential.id == credential_id)
    )
    return result.scalar_one_or_none()


async def get_credentials_by_user_id(
    db: AsyncSession, user_id: uuid.UUID
) -> List[Credential]:
    """Fetch all credentials belonging to a user, newest first."""
    result = await db.execute(
        select(Credential)
        .where(Credential.user_id == user_id)
        .order_by(Credential.created_at.desc())
    )
    return list(result.scalars().all())


async def get_credential_count_by_user(
    db: AsyncSession, user_id: uuid.UUID
) -> int:
    """Count credentials for a user."""
    result = await db.execute(
        select(func.count()).select_from(Credential).where(Credential.user_id == user_id)
    )
    return result.scalar() or 0
