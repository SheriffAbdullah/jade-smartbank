"""Loan schemas for loan applications."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EMICalculationRequest(BaseModel):
    """EMI calculation request schema."""

    loan_type: str = Field(..., description="Loan type: personal, home, auto, education")
    principal_amount: Decimal = Field(..., gt=0, description="Loan principal amount")
    interest_rate: Optional[Decimal] = Field(None, gt=0, le=100, description="Annual interest rate (optional, uses default if not provided)")
    tenure_months: int = Field(..., gt=0, le=360, description="Tenure in months")

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: str) -> str:
        """Validate loan type."""
        valid_types = ["personal", "home", "auto", "education"]
        if v.lower() not in valid_types:
            raise ValueError(f"Loan type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "loan_type": "personal",
                "principal_amount": 500000.00,
                "interest_rate": 12.5,
                "tenure_months": 36,
            }
        }


class EMIBreakdown(BaseModel):
    """EMI breakdown for a single month."""

    month: int
    emi: Decimal
    principal: Decimal
    interest: Decimal
    balance: Decimal

    class Config:
        json_encoders = {Decimal: float}


class EMICalculationResponse(BaseModel):
    """EMI calculation response schema."""

    loan_type: str
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    total_interest: Decimal
    total_payable: Decimal
    amortization_schedule: list[dict]

    class Config:
        json_encoders = {Decimal: float}


class LoanApplicationRequest(BaseModel):
    """Loan application request schema."""

    loan_type: str = Field(
        ..., description="Loan type: personal, home, auto, education"
    )
    principal_amount: Decimal = Field(..., gt=0, description="Loan principal amount")
    interest_rate: Optional[Decimal] = Field(None, gt=0, le=100, description="Annual interest rate (optional)")
    tenure_months: int = Field(..., gt=0, le=360, description="Loan tenure in months")
    purpose: Optional[str] = Field(None, max_length=200, description="Purpose of loan")
    disbursement_account_id: Optional[str] = Field(None, description="Account UUID for disbursement")

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: str) -> str:
        """Validate loan type."""
        valid_types = ["personal", "home", "auto", "education"]
        if v.lower() not in valid_types:
            raise ValueError(f"Loan type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "loan_type": "personal",
                "principal_amount": 500000.00,
                "interest_rate": 12.5,
                "tenure_months": 36,
                "purpose": "Home renovation"
            }
        }


class LoanApplicationResponse(BaseModel):
    """Loan application response schema."""

    loan_id: str
    loan_type: str
    loan_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    total_payable: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class LoanResponse(BaseModel):
    """Loan details response schema."""

    id: str
    user_id: str
    loan_type: str
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    total_interest: Decimal
    total_payable: Decimal
    outstanding_amount: Optional[Decimal] = None
    emis_paid: int
    disbursement_account_id: Optional[str] = None
    purpose: Optional[str] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class EMIPaymentResponse(BaseModel):
    """EMI payment response schema."""

    emi_number: int
    due_date: date
    emi_amount: Decimal
    payment_status: str
    paid_amount: Optional[Decimal] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class PayEMIRequest(BaseModel):
    """Pay EMI request schema."""

    account_id: str = Field(..., description="Account UUID to debit from")
    emi_number: int = Field(..., ge=1, description="EMI installment number")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "emi_number": 1,
            }
        }


class LoanApprovalRequest(BaseModel):
    """Loan approval/rejection request schema for admin."""

    action: str = Field(..., description="Action: approve or reject")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Rejection reason (required if rejecting)")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action."""
        valid_actions = ["approve", "reject"]
        if v.lower() not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "action": "approve",
                "rejection_reason": None
            }
        }


class LoanEMIPaymentRequest(BaseModel):
    """EMI payment request schema."""

    payment_account_id: str = Field(..., description="Account UUID to debit payment from")
    emi_number: int = Field(..., ge=1, description="EMI installment number to pay")
    amount: Decimal = Field(..., gt=0, description="Payment amount")

    class Config:
        json_schema_extra = {
            "example": {
                "payment_account_id": "550e8400-e29b-41d4-a716-446655440000",
                "emi_number": 1,
                "amount": 16607.97
            }
        }


class LoanEMIPaymentResponse(BaseModel):
    """EMI payment response schema."""

    id: str
    loan_id: str
    emi_number: int
    amount_paid: Decimal
    payment_reference: str
    paid_at: datetime
    status: str
    message: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class EMIScheduleResponse(BaseModel):
    """EMI schedule response schema."""

    loan_id: str
    schedule: list[dict]

    class Config:
        from_attributes = True


# Aliases for backwards compatibility
LoanApplication = LoanApplicationRequest