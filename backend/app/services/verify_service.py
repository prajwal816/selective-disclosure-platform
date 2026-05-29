"""
Verification service — handles cryptographic verification of shared presentations.

Performs Merkle proof verification and Ed25519 signature validation to produce
a detailed verification report with per-field trust indicators.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import (
    Ed25519Signer,
    MerkleProofStep,
    MerkleTree,
    _compute_leaf_hash,
    create_signing_payload,
)
from app.crud.share_crud import get_by_token, increment_access_count
from app.schemas.verify import (
    FieldVerification,
    PresentationData,
    VerificationResult,
)


async def get_presentation(
    db: AsyncSession, share_token: str
) -> PresentationData:
    """
    Fetch a shared presentation and perform verification.
    
    This is the public-facing endpoint — no auth required.
    Increments the access counter and checks expiry.
    """
    presentation = await get_by_token(db, share_token)

    if not presentation:
        return PresentationData(
            share_token=share_token,
            credential_type="unknown",
            issuer_did="unknown",
            issued_at=datetime.now(timezone.utc),
            disclosed_fields={},
            expires_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            verification=VerificationResult(
                verified=False,
                status="not_found",
                message="Share link not found or has been revoked",
            ),
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    expires_at = presentation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return PresentationData(
            share_token=share_token,
            credential_type=presentation.credential_type,
            issuer_did=presentation.issuer_did,
            issued_at=presentation.credential_issued_at,
            disclosed_fields={},
            expires_at=expires_at,
            created_at=presentation.created_at,
            verification=VerificationResult(
                verified=False,
                status="expired",
                message="This share link has expired",
                credential_type=presentation.credential_type,
                issuer_did=presentation.issuer_did,
                issued_at=presentation.credential_issued_at,
                share_expires_at=expires_at,
            ),
        )

    # Check access limit
    if presentation.access_count >= presentation.max_access_count:
        return PresentationData(
            share_token=share_token,
            credential_type=presentation.credential_type,
            issuer_did=presentation.issuer_did,
            issued_at=presentation.credential_issued_at,
            disclosed_fields={},
            expires_at=expires_at,
            created_at=presentation.created_at,
            verification=VerificationResult(
                verified=False,
                status="access_limit",
                message="This share link has reached its maximum access count",
            ),
        )

    # Increment access count
    await increment_access_count(db, presentation.id)

    # Perform cryptographic verification
    verification = _verify_presentation_crypto(presentation)

    # Build disclosed fields dict from proofs
    disclosed_fields = {}
    for field_name in presentation.disclosed_fields:
        if field_name in presentation.merkle_proofs:
            disclosed_fields[field_name] = presentation.merkle_proofs[field_name]["value"]

    return PresentationData(
        share_token=share_token,
        credential_type=presentation.credential_type,
        issuer_did=presentation.issuer_did,
        issued_at=presentation.credential_issued_at,
        disclosed_fields=disclosed_fields,
        expires_at=expires_at,
        created_at=presentation.created_at,
        verification=verification,
    )


async def verify_presentation_by_token(
    db: AsyncSession, share_token: str
) -> VerificationResult:
    """
    Perform full cryptographic verification of a shared presentation.
    
    Process:
    1. Fetch presentation by token
    2. Check expiry and access limits
    3. For each disclosed field:
       a. Recompute leaf hash from (key, salt, value)
       b. Verify Merkle proof against stored root
    4. Verify Ed25519 signature on the Merkle root
    5. Compute trust score and return detailed report
    """
    presentation = await get_by_token(db, share_token)

    if not presentation:
        return VerificationResult(
            verified=False,
            status="not_found",
            message="Share link not found or has been revoked",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    expires_at = presentation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return VerificationResult(
            verified=False,
            status="expired",
            message="This share link has expired",
            credential_type=presentation.credential_type,
            issuer_did=presentation.issuer_did,
            share_expires_at=expires_at,
        )

    return _verify_presentation_crypto(presentation)


def _verify_presentation_crypto(presentation) -> VerificationResult:
    """
    Core cryptographic verification logic.
    
    Verifies each disclosed field's Merkle proof and the issuer's Ed25519 signature.
    """
    field_verifications: List[FieldVerification] = []
    disclosed_fields: Dict[str, Any] = {}
    all_proofs_valid = True
    trust_indicators: List[str] = []

    # Verify each disclosed field's Merkle proof
    for field_name in presentation.disclosed_fields:
        proof_data = presentation.merkle_proofs.get(field_name)

        if not proof_data:
            field_verifications.append(
                FieldVerification(
                    field_name=field_name,
                    value=None,
                    merkle_proof_valid=False,
                    leaf_hash="",
                    status="error",
                )
            )
            all_proofs_valid = False
            continue

        # Recompute the leaf hash from the disclosed data
        value = proof_data["value"]
        salt = proof_data["salt"]
        stored_leaf_hash = proof_data["leaf_hash"]

        recomputed_leaf = _compute_leaf_hash(field_name, salt, value)

        # Verify leaf hash matches
        leaf_matches = recomputed_leaf == stored_leaf_hash

        # Reconstruct proof steps
        proof_steps = [
            MerkleProofStep.from_dict(step)
            for step in proof_data["proof"]
        ]

        # Verify Merkle proof against the root
        proof_valid = MerkleTree.verify_proof(
            recomputed_leaf, proof_steps, presentation.merkle_root
        )

        field_valid = leaf_matches and proof_valid

        field_verifications.append(
            FieldVerification(
                field_name=field_name,
                value=value,
                merkle_proof_valid=field_valid,
                leaf_hash=recomputed_leaf,
                status="verified" if field_valid else "invalid",
            )
        )

        if field_valid:
            disclosed_fields[field_name] = value
        else:
            all_proofs_valid = False

    # Verify Ed25519 signature on the Merkle root
    issued_at_str = presentation.credential_issued_at.isoformat()
    signing_payload = create_signing_payload(
        presentation.merkle_root,
        presentation.issuer_did,
        issued_at_str,
    )

    signature_valid = Ed25519Signer.verify_with_public_key(
        data=signing_payload,
        signature_hex=presentation.signature,
        public_key_hex=presentation.public_key_hex,
    )

    # Overall verification
    overall_valid = all_proofs_valid and signature_valid

    # Build trust indicators
    if signature_valid:
        trust_indicators.append("Ed25519 digital signature verified")
    else:
        trust_indicators.append("⚠️ Digital signature verification FAILED")

    if all_proofs_valid:
        trust_indicators.append("All Merkle inclusion proofs verified")
    else:
        trust_indicators.append("⚠️ One or more Merkle proofs FAILED")

    trust_indicators.append(
        f"Credential issued by {presentation.issuer_did}"
    )
    trust_indicators.append(
        f"{len(presentation.disclosed_fields)} of total fields disclosed"
    )
    trust_indicators.append("SHA-256 hash integrity confirmed")

    # Compute trust score
    verified_count = sum(
        1 for fv in field_verifications if fv.status == "verified"
    )
    total_count = len(field_verifications)
    field_score = verified_count / total_count if total_count > 0 else 0
    sig_score = 1.0 if signature_valid else 0.0
    trust_score = round((field_score * 0.6 + sig_score * 0.4), 2)

    expires_at = presentation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return VerificationResult(
        verified=overall_valid,
        status="verified" if overall_valid else "invalid",
        message=(
            "All cryptographic proofs verified successfully. "
            "The disclosed data is authentic and untampered."
            if overall_valid
            else "Verification failed. The data may have been tampered with."
        ),
        credential_type=presentation.credential_type,
        issuer_did=presentation.issuer_did,
        issued_at=presentation.credential_issued_at,
        disclosed_fields=disclosed_fields,
        field_verifications=field_verifications,
        merkle_root=presentation.merkle_root,
        signature_valid=signature_valid,
        total_fields_disclosed=len(presentation.disclosed_fields),
        trust_score=trust_score,
        trust_indicators=trust_indicators,
        share_created_at=presentation.created_at,
        share_expires_at=expires_at,
        access_count=presentation.access_count,
    )
