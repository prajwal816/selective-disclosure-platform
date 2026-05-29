"""
SharedPresentation ORM model — stores selective disclosure presentations with Merkle proofs.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SharedPresentation(Base):
    """
    A selectively disclosed verifiable presentation.
    
    Contains only the disclosed fields, their Merkle proofs, and the
    issuer's signature on the full Merkle root — enabling verification
    without access to undisclosed fields.
    """

    __tablename__ = "shared_presentations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("credentials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Share token for public access
    share_token: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    
    # Disclosed data with proofs
    disclosed_fields: Mapped[list] = mapped_column(JSONB, nullable=False)
    merkle_proofs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Original credential crypto data (needed for verification)
    merkle_root: Mapped[str] = mapped_column(String(128), nullable=False)
    signature: Mapped[str] = mapped_column(String(256), nullable=False)
    issuer_did: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key_hex: Mapped[str] = mapped_column(String(256), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(100), nullable=False)
    credential_issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    # Access control
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    max_access_count: Mapped[int] = mapped_column(Integer, default=100)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    credential = relationship("Credential", back_populates="shared_presentations")

    @property
    def is_expired(self) -> bool:
        """Check if this share link has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_access_limit_reached(self) -> bool:
        """Check if the access count limit has been reached."""
        return self.access_count >= self.max_access_count

    def __repr__(self) -> str:
        return f"<SharedPresentation token={self.share_token[:8]}...>"
