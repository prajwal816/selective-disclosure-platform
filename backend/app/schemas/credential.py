"""
Pydantic schemas for credential issuance and retrieval.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CredentialCreate(BaseModel):
    """Request schema for issuing a new credential."""

    credential_type: str = Field(
        default="AcademicCredential",
        description="Type of credential",
        examples=["AcademicCredential", "ProfessionalCredential", "IdentityCredential"],
    )
    claims: Dict[str, Any] = Field(
        ...,
        description="Key-value pairs of credential claims",
        examples=[
            {
                "name": "Prajwal Kumar",
                "degree": "B.Tech Computer Science",
                "university": "IIT Delhi",
                "graduationYear": 2025,
                "cgpa": 8.5,
                "rollNumber": "CS2021001",
                "issuerName": "Academic Records Office",
            }
        ],
    )

    @field_validator("claims")
    @classmethod
    def validate_claims(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if len(v) < 2:
            raise ValueError("Credential must have at least 2 claims")
        if len(v) > 50:
            raise ValueError("Credential cannot have more than 50 claims")
        # Validate key names
        for key in v:
            if not key.strip():
                raise ValueError("Claim key cannot be empty")
            if len(key) > 100:
                raise ValueError(f"Claim key '{key[:20]}...' exceeds 100 characters")
        return v


class CredentialResponse(BaseModel):
    """Single credential response."""

    id: uuid.UUID
    credential_type: str
    claims: Dict[str, Any]
    merkle_root: str
    issuer_did: str
    issued_at: datetime
    status: str
    created_at: datetime
    total_claims: int = 0
    
    model_config = {"from_attributes": True}

    @classmethod
    def from_credential(cls, credential) -> "CredentialResponse":
        return cls(
            id=credential.id,
            credential_type=credential.credential_type,
            claims=credential.claims,
            merkle_root=credential.merkle_root,
            issuer_did=credential.issuer_did,
            issued_at=credential.issued_at,
            status=credential.status,
            created_at=credential.created_at,
            total_claims=len(credential.claims),
        )


class CredentialListResponse(BaseModel):
    """Paginated list of credentials."""

    credentials: List[CredentialResponse]
    total: int
