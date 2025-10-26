"""Loan schemas for loan applications."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EMICalculationRequest(BaseModel):
    """EMI calculation request schema."""

    loan_amount: Decimal = Field(..., gt=0, description="Loan amount")
    interest_rate: Decimal = Field(..., gt=0, le=100, description="Annual interest rate")
    tenure_months: int = Field(..., gt=0, le=360, description="Tenure in months")

    class Config:
        json_schema_extra = {
            "example": {
                "loan_amount": 500000.00,
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

    loan_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    total_interest: Decimal
    total_payable: Decimal
    breakdown: list[EMIBreakdown]

    class Config:
        json_encoders = {Decimal: float}


class LoanApplicationRequest(BaseModel):
    """Loan application request schema."""

    loan_type: str = Field(
        ..., description="Loan type: personal, home, vehicle, education, business"
    )
    loan_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., gt=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: str) -> str:
        """Validate loan type."""
        valid_types = ["personal", "home", "vehicle", "education", "business"]
        if v.lower() not in valid_types:
            raise ValueError(f"Loan type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "loan_type": "personal",
                "loan_amount": 500000.00,
                "interest_rate": 12.5,
                "tenure_months": 36,
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

    loan_id: str
    loan_type: str
    loan_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    total_payable: Decimal
    status: str
    outstanding_amount: Optional[Decimal] = None
    paid_amount: Decimal
    next_emi_due_date: Optional[date] = None
    disbursed_at: Optional[datetime] = None
    created_at: datetime

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