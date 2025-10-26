"""Account routes - Use Case 2.

SECURITY: Account creation and management with authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, get_current_user_id
from app.db.base import get_db
from app.schemas.account import (
    AccountCreate,
    AccountResponse,
    AccountStatementRequest,
    AccountStatementResponse,
    TransactionItem,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create bank account",
)
async def create_account(
    data: AccountCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """Create a new bank account."""
    try:
        account = AccountService.create_account(db, user_id, data, ip_address)
        return AccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[AccountResponse], summary="List user accounts")
async def list_accounts(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get all accounts for logged-in user."""
    accounts = AccountService.get_user_accounts(db, user_id)
    return [AccountResponse.model_validate(acc) for acc in accounts]


@router.get("/{account_id}", response_model=AccountResponse, summary="Get account details")
async def get_account(
    account_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get specific account details."""
    try:
        account = AccountService.get_account(db, account_id, user_id)
        return AccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{account_id}/statement",
    response_model=AccountStatementResponse,
    summary="Get account statement",
)
async def get_statement(
    account_id: str,
    params: AccountStatementRequest = Depends(),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get account statement with transactions."""
    try:
        account, transactions, total = AccountService.get_account_statement(
            db,
            account_id,
            user_id,
            params.start_date,
            params.end_date,
            params.page,
            params.limit,
        )

        return AccountStatementResponse(
            account_number=account.account_number,
            period={"start_date": str(params.start_date), "end_date": str(params.end_date)},
            opening_balance=account.balance,
            closing_balance=account.balance,
            transactions=[
                TransactionItem(
                    transaction_id=str(txn.id),
                    date=txn.created_at,
                    type="credit"
                    if txn.to_account_id == account_id
                    else "debit",
                    description=txn.description or txn.transaction_type,
                    amount=txn.amount,
                    balance=account.balance,  # Simplified
                    reference=txn.reference_number,
                )
                for txn in transactions
            ],
            pagination={
                "page": params.page,
                "limit": params.limit,
                "total": total,
                "pages": (total + params.limit - 1) // params.limit,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
