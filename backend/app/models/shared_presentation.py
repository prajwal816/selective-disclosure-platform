"""
SharedPresentation ORM model — stores selective disclosure presentations with Merkle proofs.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, func, JSON
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

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    credential_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("credentials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Share token for public access
    share_token: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )

    # Disclosed data with proofs
    disclosed_fields: Mapped[list] = mapped_column(JSON, nullable=False)
    merkle_proofs: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Original credential crypto data (needed for verification)
    merkle_root: Mapped[str] = mapped_column(String(128), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    issuer_did: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key_hex: Mapped[str] = mapped_column(Text, nullable=False)
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
        from datetime import timezone
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    @property
    def is_access_limit_reached(self) -> bool:
        """Check if the access count limit has been reached."""
        return self.access_count >= self.max_access_count

    def __repr__(self) -> str:
        return f"<SharedPresentation token={self.share_token[:8]}...>"
