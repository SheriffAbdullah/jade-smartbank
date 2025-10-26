"""Pydantic schemas for request/response validation."""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.account import (
    AccountCreate,
    AccountResponse,
    AccountStatementRequest,
    AccountStatementResponse,
)
from app.schemas.transaction import (
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)
from app.schemas.loan import (
    EMICalculationRequest,
    EMICalculationResponse,
    LoanApplicationRequest,
    LoanApplicationResponse,
    LoanResponse,
    PayEMIRequest,
)
from app.schemas.kyc import (
    KYCDocumentResponse,
    KYCDocumentUpload,
    KYCStatusResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    # KYC
    "KYCDocumentUpload",
    "KYCDocumentResponse",
    "KYCStatusResponse",
    # Account
    "AccountCreate",
    "AccountResponse",
    "AccountStatementRequest",
    "AccountStatementResponse",
    # Transaction
    "TransferRequest",
    "DepositRequest",
    "WithdrawRequest",
    "TransactionResponse",
    # Loan
    "EMICalculationRequest",
    "EMICalculationResponse",
    "LoanApplicationRequest",
    "LoanApplicationResponse",
    "LoanResponse",
    "PayEMIRequest",
]