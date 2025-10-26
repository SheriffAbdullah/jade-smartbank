"""Refresh Token model for JWT token management.

SECURITY: Secure storage and revocation of refresh tokens.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    """Refresh Token model for JWT authentication.

    SECURITY: Stores hashed tokens, not plain text.
    """

    __tablename__ = "refresh_tokens"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Expiry
    expires_at = Column(DateTime, nullable=False, index=True)

    # Status
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)

    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken {self.id}>"