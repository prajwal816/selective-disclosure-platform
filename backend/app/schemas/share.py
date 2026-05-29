"""
Pydantic schemas for selective disclosure sharing.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ShareRequest(BaseModel):
    """Request to create a selective disclosure share."""

    credential_id: str = Field(
        ..., description="ID of the credential to share"
    )
    selected_fields: List[str] = Field(
        ...,
        description="List of claim keys to disclose",
        min_length=1,
    )
    expiry_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=720,  # Max 30 days
        description="Share link expiry in hours (1-720)",
    )

    @field_validator("selected_fields")
    @classmethod
    def validate_selected_fields(cls, v: List[str]) -> List[str]:
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for field in v:
            if field not in seen:
                seen.add(field)
                unique.append(field)
        return unique


class ShareResponse(BaseModel):
    """Response after creating a share."""

    share_token: str
    share_url: str
    qr_data: str
    expires_at: datetime
    disclosed_fields: List[str]
    total_original_fields: int


class ShareListItem(BaseModel):
    """Summary of a shared presentation."""

    id: str
    share_token: str
    credential_id: str
    credential_type: str
    disclosed_fields: List[str]
    expires_at: datetime
    access_count: int
    max_access_count: int
    created_at: datetime
    is_expired: bool

    model_config = {"from_attributes": True}


class ShareListResponse(BaseModel):
    """List of user's shared presentations."""

    shares: List[ShareListItem]
    total: int
