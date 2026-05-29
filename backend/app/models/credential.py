"""
Credential ORM model — stores issued verifiable credentials with cryptographic metadata.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Credential(Base):
    """
    A verifiable credential issued by a holder.
    
    Stores the full claims, per-claim salts, Merkle root, Ed25519 signature,
    and metadata. The salts and full claims are only accessible to the owner.
    """

    __tablename__ = "credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Credential content
    credential_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="AcademicCredential"
    )
    claims: Mapped[dict] = mapped_column(JSONB, nullable=False)
    salts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Cryptographic data
    merkle_root: Mapped[str] = mapped_column(String(128), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    issuer_did: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key_hex: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tree structure (stored for proof generation)
    tree_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Metadata
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="credentials")
    shared_presentations = relationship(
        "SharedPresentation", back_populates="credential", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Credential {self.id} type={self.credential_type}>"
