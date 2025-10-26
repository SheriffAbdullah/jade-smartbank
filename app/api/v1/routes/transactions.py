"""Transaction management endpoints.

SECURITY: All routes require authentication. Validates account ownership and limits.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, get_current_user_id
from app.db.base import get_db
from app.models import User
from app.schemas.transaction import (
    DepositRequest,
    DepositResponse,
    TransactionFilter,
    TransactionResponse,
    TransferRequest,
    TransferResponse,
    WithdrawRequest,
    WithdrawResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/transfer", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def transfer_money(
    request: Request,
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Transfer money between accounts.

    **SECURITY**: Validates account ownership, balance, daily limits, minimum balance.

    **Business Rules**:
    - Source account must belong to authenticated user
    - Both accounts must be active
    - Amount must be positive
    - Sufficient balance after maintaining minimum balance
    - Daily transfer limit not exceeded
    - Cannot transfer to same account

    **Returns**: Transaction details with reference number
    """
    try:
        transaction = TransactionService.transfer_money(
            db=db, user_id=str(current_user.id), request=data, ip_address=ip_address
        )

        return TransferResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            amount=transaction.amount,
            description=transaction.description,
            reference_number=transaction.reference_number,
            status=transaction.status,
            created_at=transaction.created_at,
            message="Transfer successful",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transfer failed. Please try again.",
        )


@router.post("/deposit", response_model=DepositResponse, status_code=status.HTTP_201_CREATED)
async def deposit_money(
    request: Request,
    data: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Deposit money to account.

    **SECURITY**: Validates account ownership and status.

    **Business Rules**:
    - Account must belong to authenticated user
    - Account must be active
    - Amount must be positive

    **Returns**: Deposit transaction details
    """
    try:
        transaction = TransactionService.deposit_money(
            db=db, user_id=str(current_user.id), request=data, ip_address=ip_address
        )

        return DepositResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            account_id=transaction.to_account_id,
            amount=transaction.amount,
            description=transaction.description,
            reference_number=transaction.reference_number,
            status=transaction.status,
            created_at=transaction.created_at,
            message="Deposit successful",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deposit failed. Please try again.",
        )


@router.post("/withdraw", response_model=WithdrawResponse, status_code=status.HTTP_201_CREATED)
async def withdraw_money(
    request: Request,
    data: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Withdraw money from account.

    **SECURITY**: Validates account ownership, balance, minimum balance.

    **Business Rules**:
    - Account must belong to authenticated user
    - Account must be active
    - Amount must be positive
    - Sufficient balance after maintaining minimum balance

    **Returns**: Withdrawal transaction details
    """
    try:
        transaction = TransactionService.withdraw_money(
            db=db, user_id=str(current_user.id), request=data, ip_address=ip_address
        )

        return WithdrawResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            account_id=transaction.from_account_id,
            amount=transaction.amount,
            description=transaction.description,
            reference_number=transaction.reference_number,
            status=transaction.status,
            created_at=transaction.created_at,
            message="Withdrawal successful",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Withdrawal failed. Please try again.",
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transaction details by ID.

    **SECURITY**: Only returns transactions involving user's accounts.

    **Returns**: Complete transaction details including before/after balances
    """
    try:
        transaction = TransactionService.get_transaction(
            db=db, user_id=str(current_user.id), transaction_id=transaction_id
        )

        return TransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            amount=transaction.amount,
            description=transaction.description,
            reference_number=transaction.reference_number,
            status=transaction.status,
            from_balance_before=transaction.from_balance_before,
            from_balance_after=transaction.from_balance_after,
            to_balance_before=transaction.to_balance_before,
            to_balance_after=transaction.to_balance_after,
            is_flagged=transaction.is_flagged,
            fraud_score=transaction.fraud_score,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction",
        )


@router.get("", response_model=List[TransactionResponse])
async def get_transaction_history(
    account_id: Optional[UUID] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transaction history with optional filters.

    **SECURITY**: Only returns transactions involving user's accounts.

    **Query Parameters**:
    - `account_id`: Filter by specific account
    - `transaction_type`: Filter by type (transfer, deposit, withdrawal)
    - `start_date`: Filter from date (YYYY-MM-DD)
    - `end_date`: Filter to date (YYYY-MM-DD)
    - `min_amount`: Minimum transaction amount
    - `max_amount`: Maximum transaction amount
    - `skip`: Pagination offset (default: 0)
    - `limit`: Page size (default: 50, max: 100)

    **Returns**: List of transactions ordered by date (newest first)
    """
    try:
        # Build filters
        from datetime import datetime
        from decimal import Decimal

        filters = None
        if any([account_id, transaction_type, start_date, end_date, min_amount, max_amount]):
            filters = TransactionFilter(
                account_id=account_id,
                transaction_type=transaction_type,
                start_date=datetime.fromisoformat(start_date).date() if start_date else None,
                end_date=datetime.fromisoformat(end_date).date() if end_date else None,
                min_amount=Decimal(str(min_amount)) if min_amount else None,
                max_amount=Decimal(str(max_amount)) if max_amount else None,
            )

        # Limit page size
        limit = min(limit, 100)

        transactions = TransactionService.get_transaction_history(
            db=db, user_id=str(current_user.id), filters=filters, skip=skip, limit=limit
        )

        return [
            TransactionResponse(
                id=t.id,
                transaction_type=t.transaction_type,
                from_account_id=t.from_account_id,
                to_account_id=t.to_account_id,
                amount=t.amount,
                description=t.description,
                reference_number=t.reference_number,
                status=t.status,
                from_balance_before=t.from_balance_before,
                from_balance_after=t.from_balance_after,
                to_balance_before=t.to_balance_before,
                to_balance_after=t.to_balance_after,
                is_flagged=t.is_flagged,
                fraud_score=t.fraud_score,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in transactions
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history",
        )