"""KYC Document model for identity verification.

SECURITY: Stores document information, not the actual document files.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class KYCDocument(Base):
    """KYC Document model for user verification.

    SECURITY: Document verification status tracked with admin approval.
    """

    __tablename__ = "kyc_documents"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document Details
    document_type = Column(
        String(50), nullable=False
    )  # pan, aadhaar, passport, driving_license
    document_number = Column(String(50), nullable=False)
    document_url = Column(String(500))  # Simulated: path to uploaded file

    # Verification
    is_verified = Column(Boolean, default=False, index=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="kyc_documents", foreign_keys=[user_id])

    def __repr__(self):
        return f"<KYCDocument {self.document_type} - {self.document_number}>"