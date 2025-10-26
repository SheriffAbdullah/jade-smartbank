"""Loan EMI Payment model for tracking installments.

SECURITY: Tracks individual EMI payments with due dates and penalties.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class LoanEMIPayment(Base):
    """Loan EMI Payment model for monthly installments.

    SECURITY: Immutable payment records with late fee tracking.
    """

    __tablename__ = "loan_emi_payments"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))

    # EMI Details
    emi_number = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)

    # Payment
    paid_amount = Column(Numeric(15, 2))
    paid_at = Column(DateTime)
    payment_status = Column(
        String(20), default="pending", index=True
    )  # pending, paid, overdue, partial

    # Late Fee
    late_fee = Column(Numeric(10, 2), default=Decimal("0.00"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    loan = relationship("Loan", back_populates="emi_payments")

    def __repr__(self):
        return f"<LoanEMIPayment {self.emi_number} - {self.payment_status}>"