"""Audit Log model for security and compliance tracking.

SECURITY: Immutable audit trail for all critical operations.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditLog(Base):
    """Audit Log model for tracking all security-relevant events.

    SECURITY: Append-only audit trail with complete context.
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Action Details
    action = Column(String(100), nullable=False, index=True)
    level = Column(String(20), default="info")  # info, warning, error, critical

    # User Context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Resource
    resource_type = Column(String(50), index=True)
    resource_id = Column(UUID(as_uuid=True), index=True)

    # Details
    details = Column(JSONB)
    success = Column(Boolean, default=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} - {self.created_at}>"