"""Account model for bank accounts.

SECURITY: Balance tracking with available_balance for pending transactions.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Account(Base):
    """Bank account model for savings, current, and FD accounts.

    SECURITY: Tracks balance, limits, and account status.
    """

    __tablename__ = "accounts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Account Details
    account_number = Column(String(18), unique=True, nullable=False, index=True)
    account_type = Column(String(20), nullable=False)  # savings, current, fd
    ifsc_code = Column(String(11), default="JADE0000001")

    # Balance
    balance = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    available_balance = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Limits
    daily_transfer_limit = Column(Numeric(15, 2), default=Decimal("100000.00"))
    min_balance = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Interest (for FD)
    interest_rate = Column(Numeric(5, 2))  # For FD accounts
    maturity_date = Column(Date)  # For FD accounts

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_frozen = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions_from = relationship(
        "Transaction",
        back_populates="from_account",
        foreign_keys="Transaction.from_account_id"
    )
    transactions_to = relationship(
        "Transaction",
        back_populates="to_account",
        foreign_keys="Transaction.to_account_id"
    )
    transfer_tracking = relationship("DailyTransferTracking", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account {self.account_number} - {self.account_type}>"