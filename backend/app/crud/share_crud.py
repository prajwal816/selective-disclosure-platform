"""
CRUD operations for the SharedPresentation model.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shared_presentation import SharedPresentation


async def create_shared_presentation(
    db: AsyncSession,
    credential_id: uuid.UUID,
    share_token: str,
    disclosed_fields: list,
    merkle_proofs: dict,
    merkle_root: str,
    signature: str,
    issuer_did: str,
    public_key_hex: str,
    credential_type: str,
    credential_issued_at,
    expires_at,
    max_access_count: int = 100,
) -> SharedPresentation:
    """Create a new shared presentation record."""
    presentation = SharedPresentation(
        credential_id=credential_id,
        share_token=share_token,
        disclosed_fields=disclosed_fields,
        merkle_proofs=merkle_proofs,
        merkle_root=merkle_root,
        signature=signature,
        issuer_did=issuer_did,
        public_key_hex=public_key_hex,
        credential_type=credential_type,
        credential_issued_at=credential_issued_at,
        expires_at=expires_at,
        max_access_count=max_access_count,
    )
    db.add(presentation)
    await db.flush()
    await db.refresh(presentation)
    return presentation


async def get_by_token(
    db: AsyncSession, share_token: str
) -> Optional[SharedPresentation]:
    """Fetch a shared presentation by its share token."""
    result = await db.execute(
        select(SharedPresentation).where(
            SharedPresentation.share_token == share_token
        )
    )
    return result.scalar_one_or_none()


async def increment_access_count(
    db: AsyncSession, presentation_id: uuid.UUID
) -> None:
    """Increment the access counter for a presentation."""
    await db.execute(
        update(SharedPresentation)
        .where(SharedPresentation.id == presentation_id)
        .values(access_count=SharedPresentation.access_count + 1)
    )
    await db.flush()


async def get_shares_by_credential_id(
    db: AsyncSession, credential_id: uuid.UUID
) -> List[SharedPresentation]:
    """Fetch all shares for a specific credential."""
    result = await db.execute(
        select(SharedPresentation)
        .where(SharedPresentation.credential_id == credential_id)
        .order_by(SharedPresentation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_shares_by_user_credentials(
    db: AsyncSession, credential_ids: List[uuid.UUID]
) -> List[SharedPresentation]:
    """Fetch all shares for a list of credential IDs (user's credentials)."""
    if not credential_ids:
        return []
    result = await db.execute(
        select(SharedPresentation)
        .where(SharedPresentation.credential_id.in_(credential_ids))
        .order_by(SharedPresentation.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_by_token(
    db: AsyncSession, share_token: str, credential_ids: List[uuid.UUID]
) -> bool:
    """Delete a share by token, verifying ownership via credential IDs."""
    result = await db.execute(
        delete(SharedPresentation).where(
            SharedPresentation.share_token == share_token,
            SharedPresentation.credential_id.in_(credential_ids),
        )
    )
    await db.flush()
    return result.rowcount > 0


async def get_share_count_by_user_credentials(
    db: AsyncSession, credential_ids: List[uuid.UUID]
) -> int:
    """Count active shares for a user's credentials."""
    if not credential_ids:
        return 0
    result = await db.execute(
        select(func.count())
        .select_from(SharedPresentation)
        .where(SharedPresentation.credential_id.in_(credential_ids))
    )
    return result.scalar() or 0
