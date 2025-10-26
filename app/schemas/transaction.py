"""Transaction schemas for money transfers."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.validation import validate_account_number, validate_ifsc_code


class TransferRequest(BaseModel):
    """Money transfer request schema."""

    from_account_id: str = Field(..., description="Source account UUID")
    to_account_number: str = Field(..., description="Beneficiary account number")
    to_ifsc_code: str = Field(..., description="Beneficiary IFSC code")
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    description: Optional[str] = Field(None, max_length=500)
    beneficiary_name: str = Field(..., max_length=200)

    @field_validator("to_account_number")
    @classmethod
    def validate_account(cls, v: str) -> str:
        """Validate account number format."""
        if not validate_account_number(v):
            raise ValueError("Invalid account number format")
        return v

    @field_validator("to_ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        """Validate IFSC code format."""
        if not validate_ifsc_code(v):
            raise ValueError("Invalid IFSC code format")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "from_account_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_account_number": "JADE00019876543210",
                "to_ifsc_code": "JADE0000001",
                "amount": 5000.00,
                "description": "Payment for services",
                "beneficiary_name": "Priya Sharma",
            }
        }


class DepositRequest(BaseModel):
    """Deposit request schema."""

    account_id: str = Field(..., description="Account UUID")
    amount: Decimal = Field(..., gt=0, description="Deposit amount")
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 10000.00,
                "description": "Cash deposit",
            }
        }


class WithdrawRequest(BaseModel):
    """Withdrawal request schema."""

    account_id: str = Field(..., description="Account UUID")
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount")
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 5000.00,
                "description": "ATM withdrawal",
            }
        }


class TransactionResponse(BaseModel):
    """Transaction response schema."""

    transaction_id: str
    reference_number: str
    transaction_type: str
    transaction_status: str
    amount: Decimal
    from_account: Optional[str] = None
    to_account: Optional[str] = None
    beneficiary_name: Optional[str] = None
    description: Optional[str] = None
    is_flagged: bool
    fraud_score: Optional[Decimal] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class TransferResponse(TransactionResponse):
    """Money transfer response schema."""
    pass


class DepositResponse(TransactionResponse):
    """Deposit response schema."""
    pass


class WithdrawResponse(TransactionResponse):
    """Withdrawal response schema."""
    pass


class TransactionFilter(BaseModel):
    """Transaction filter schema for querying."""

    transaction_type: Optional[str] = None
    transaction_status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_type": "transfer",
                "transaction_status": "completed",
                "start_date": "2025-01-01T00:00:00",
                "end_date": "2025-12-31T23:59:59",
                "min_amount": 1000.00,
                "max_amount": 50000.00,
            }
        }