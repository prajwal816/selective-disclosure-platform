"""
Pydantic schemas for credential verification.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldVerification(BaseModel):
    """Verification result for a single disclosed field."""

    field_name: str
    value: Any
    merkle_proof_valid: bool
    leaf_hash: str
    status: str = Field(
        description="'verified', 'invalid', or 'error'"
    )


class VerificationResult(BaseModel):
    """Complete verification report for a shared presentation."""

    # Overall status
    verified: bool = Field(description="Overall verification status")
    status: str = Field(
        description="'verified', 'invalid', 'expired', or 'error'"
    )
    message: str

    # Credential info
    credential_type: Optional[str] = None
    issuer_did: Optional[str] = None
    issued_at: Optional[datetime] = None

    # Field-level verification
    disclosed_fields: Optional[Dict[str, Any]] = None
    field_verifications: Optional[List[FieldVerification]] = None

    # Cryptographic details
    merkle_root: Optional[str] = None
    signature_valid: Optional[bool] = None
    total_fields_disclosed: Optional[int] = None

    # Trust indicators
    trust_score: Optional[float] = Field(
        default=None,
        description="Trust score from 0.0 to 1.0",
    )
    trust_indicators: Optional[List[str]] = None

    # Share metadata
    share_created_at: Optional[datetime] = None
    share_expires_at: Optional[datetime] = None
    access_count: Optional[int] = None


class PresentationData(BaseModel):
    """Public presentation data returned for a share token."""

    share_token: str
    credential_type: str
    issuer_did: str
    issued_at: datetime
    disclosed_fields: Dict[str, Any]
    expires_at: datetime
    created_at: datetime
    verification: VerificationResult
