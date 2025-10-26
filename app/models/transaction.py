"""Transaction model for all financial operations.

SECURITY: Complete audit trail with before/after balances and fraud detection.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Transaction(Base):
    """Transaction model for transfers, deposits, and withdrawals.

    SECURITY: Immutable transaction records with complete audit trail.
    """

    __tablename__ = "transactions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Transaction Details
    transaction_type = Column(
        String(20), nullable=False
    )  # transfer, deposit, withdrawal, loan_disbursement, emi_payment
    transaction_status = Column(
        String(20), default="pending", index=True
    )  # pending, completed, failed, reversed

    # Accounts
    from_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True)
    to_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True)

    # Amount
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="INR")

    # Transfer Details (for transfers)
    beneficiary_name = Column(String(200))
    beneficiary_account = Column(String(18))
    beneficiary_ifsc = Column(String(11))

    # Metadata
    description = Column(Text)
    reference_number = Column(String(50), unique=True, nullable=False, index=True)
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Fraud Detection
    is_flagged = Column(Boolean, default=False, index=True)
    fraud_score = Column(Numeric(5, 2))  # 0-100
    flagged_reason = Column(Text)

    # Balances (for audit)
    from_balance_before = Column(Numeric(15, 2))
    from_balance_after = Column(Numeric(15, 2))
    to_balance_before = Column(Numeric(15, 2))
    to_balance_after = Column(Numeric(15, 2))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)

    # Relationships
    from_account = relationship(
        "Account",
        back_populates="transactions_from",
        foreign_keys=[from_account_id]
    )
    to_account = relationship(
        "Account",
        back_populates="transactions_to",
        foreign_keys=[to_account_id]
    )

    def __repr__(self):
        return f"<Transaction {self.reference_number} - {self.transaction_type}>"