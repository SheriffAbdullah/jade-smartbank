"""Daily transfer tracking model for limit enforcement.

SECURITY: Tracks daily transfer amounts per account.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class DailyTransferTracking(Base):
    """Daily transfer tracking for enforcing daily limits.

    SECURITY: Prevents exceeding daily transfer limits.
    """

    __tablename__ = "daily_transfer_tracking"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Tracking
    transfer_date = Column(Date, nullable=False, index=True)
    total_transferred = Column(Numeric(15, 2), default=Decimal("0.00"))
    transaction_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="transfer_tracking")

    def __repr__(self):
        return f"<DailyTransferTracking {self.transfer_date} - ₹{self.total_transferred}>"