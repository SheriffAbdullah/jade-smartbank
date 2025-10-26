"""Loan model for loan applications and management.

SECURITY: Complete loan lifecycle tracking with approval workflow.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Loan(Base):
    """Loan model for personal, home, vehicle, education, and business loans.

    SECURITY: Tracks loan status and repayment progress.
    """

    __tablename__ = "loans"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    # Loan Details
    loan_type = Column(
        String(50), nullable=False
    )  # personal, home, vehicle, education, business
    loan_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)

    # EMI Calculation
    emi_amount = Column(Numeric(15, 2), nullable=False)
    total_payable = Column(Numeric(15, 2), nullable=False)

    # Status
    status = Column(
        String(20), default="pending", index=True
    )  # pending, approved, rejected, disbursed, closed

    # Approval
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Disbursement
    disbursed_at = Column(DateTime)
    disbursement_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    # Repayment
    outstanding_amount = Column(Numeric(15, 2))
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    next_emi_due_date = Column(Date)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="loans", foreign_keys=[user_id])
    emi_payments = relationship("LoanEMIPayment", back_populates="loan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Loan {self.loan_type} - ₹{self.loan_amount}>"