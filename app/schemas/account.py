"""Account schemas for bank accounts."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AccountCreate(BaseModel):
    """Account creation request schema."""

    account_type: str = Field(..., description="Account type: savings, current, fd")
    initial_deposit: Decimal = Field(..., ge=0, description="Initial deposit amount")

    # FD specific fields
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    maturity_date: Optional[date] = None

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        """Validate account type."""
        valid_types = ["savings", "current", "fd"]
        if v.lower() not in valid_types:
            raise ValueError(f"Account type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @field_validator("initial_deposit")
    @classmethod
    def validate_initial_deposit(cls, v: Decimal, info) -> Decimal:
        """Validate minimum initial deposit based on account type."""
        account_type = info.data.get("account_type", "").lower()

        min_deposits = {"savings": Decimal("500"), "current": Decimal("5000"), "fd": Decimal("10000")}

        min_required = min_deposits.get(account_type, Decimal("0"))
        if v < min_required:
            raise ValueError(f"Minimum deposit for {account_type} account is ₹{min_required}")

        return v

    class Config:
        json_schema_extra = {
            "example": {"account_type": "savings", "initial_deposit": 5000.00}
        }


class AccountResponse(BaseModel):
    """Account response schema."""

    id: str
    account_number: str
    account_type: str
    ifsc_code: str
    balance: Decimal
    available_balance: Decimal
    daily_transfer_limit: Decimal
    min_balance: Decimal
    is_active: bool
    is_frozen: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class AccountStatementRequest(BaseModel):
    """Account statement request schema."""

    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate date range."""
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("end_date must be after start_date")
        return v


class TransactionItem(BaseModel):
    """Transaction item in statement."""

    transaction_id: str
    date: datetime
    type: str
    description: str
    amount: Decimal
    balance: Decimal
    reference: str

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}


class AccountStatementResponse(BaseModel):
    """Account statement response schema."""

    account_number: str
    period: dict
    opening_balance: Decimal
    closing_balance: Decimal
    transactions: list[TransactionItem]
    pagination: dict

    class Config:
        json_encoders = {Decimal: float}