"""Transaction service for money transfers, deposits, and withdrawals.

SECURITY: Implements atomic balance updates, daily limit tracking, minimum balance checks.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditLogger
from app.models import Account, DailyTransferTracking, Transaction
from app.schemas.transaction import (
    DepositRequest,
    TransactionFilter,
    TransferRequest,
    WithdrawRequest,
)
from app.utils import generate_reference_number


class TransactionService:
    """Transaction management service."""

    @staticmethod
    def transfer_money(
        db: Session, user_id: str, request: TransferRequest, ip_address: str
    ) -> Transaction:
        """Transfer money between accounts.

        SECURITY: Validates account ownership, balance, daily limits, minimum balance.

        Args:
            db: Database session
            user_id: User ID initiating transfer
            request: Transfer request data
            ip_address: Client IP address

        Returns:
            Transaction: Created transaction record

        Raises:
            ValueError: If validation fails
        """
        # Get source account
        from_account = (
            db.query(Account)
            .filter(Account.id == request.from_account_id, Account.user_id == user_id)
            .first()
        )

        if not from_account:
            raise ValueError("Source account not found or unauthorized")

        # Check account status
        if from_account.status != "active":
            raise ValueError(f"Source account is {from_account.status}")

        # Get destination account
        to_account = db.query(Account).filter(Account.id == request.to_account_id).first()

        if not to_account:
            raise ValueError("Destination account not found")

        if to_account.status != "active":
            raise ValueError(f"Destination account is {to_account.status}")

        # Prevent self-transfer
        if from_account.id == to_account.id:
            raise ValueError("Cannot transfer to the same account")

        # Validate amount
        if request.amount <= 0:
            raise ValueError("Transfer amount must be positive")

        # Check sufficient balance (including minimum balance requirement)
        min_balance = from_account.minimum_balance or Decimal("0.00")
        available = from_account.balance - min_balance

        if available < request.amount:
            raise ValueError(
                f"Insufficient balance. Available: ₹{available}, Required: ₹{request.amount}"
            )

        # Check daily transfer limit
        today = datetime.utcnow().date()
        daily_tracking = (
            db.query(DailyTransferTracking)
            .filter(
                DailyTransferTracking.account_id == from_account.id,
                DailyTransferTracking.date == today,
            )
            .first()
        )

        if daily_tracking:
            remaining = from_account.daily_transfer_limit - daily_tracking.total_transferred
            if remaining < request.amount:
                raise ValueError(
                    f"Daily transfer limit exceeded. Remaining: ₹{remaining}"
                )
            daily_tracking.total_transferred += request.amount
            daily_tracking.transfer_count += 1
        else:
            # Create new tracking record
            if request.amount > from_account.daily_transfer_limit:
                raise ValueError(
                    f"Amount exceeds daily limit of ₹{from_account.daily_transfer_limit}"
                )
            daily_tracking = DailyTransferTracking(
                account_id=from_account.id,
                date=today,
                total_transferred=request.amount,
                transfer_count=1,
            )
            db.add(daily_tracking)

        # Record balances before transaction
        from_balance_before = from_account.balance
        to_balance_before = to_account.balance

        # Update balances (atomic operation)
        from_account.balance -= request.amount
        from_account.available_balance = from_account.balance - min_balance
        to_account.balance += request.amount
        to_account.available_balance = to_account.balance - (
            to_account.minimum_balance or Decimal("0.00")
        )

        # Create transaction record
        transaction = Transaction(
            transaction_type="transfer",
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            amount=request.amount,
            description=request.description or "Fund transfer",
            reference_number=generate_reference_number("TXN"),
            status="completed",
            from_balance_before=from_balance_before,
            from_balance_after=from_account.balance,
            to_balance_before=to_balance_before,
            to_balance_after=to_account.balance,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.TRANSACTION_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="transaction",
            resource_id=str(transaction.id),
            details={
                "type": "transfer",
                "amount": str(request.amount),
                "from_account": str(from_account.account_number),
                "to_account": str(to_account.account_number),
                "reference": transaction.reference_number,
            },
        )

        return transaction

    @staticmethod
    def deposit_money(
        db: Session, user_id: str, request: DepositRequest, ip_address: str
    ) -> Transaction:
        """Deposit money to account.

        SECURITY: Validates account ownership and status.

        Args:
            db: Database session
            user_id: User ID
            request: Deposit request data
            ip_address: Client IP address

        Returns:
            Transaction: Created transaction record

        Raises:
            ValueError: If validation fails
        """
        # Get account
        account = (
            db.query(Account)
            .filter(Account.id == request.account_id, Account.user_id == user_id)
            .first()
        )

        if not account:
            raise ValueError("Account not found or unauthorized")

        if account.status != "active":
            raise ValueError(f"Account is {account.status}")

        # Validate amount
        if request.amount <= 0:
            raise ValueError("Deposit amount must be positive")

        # Record balance before
        balance_before = account.balance

        # Update balance
        account.balance += request.amount
        account.available_balance = account.balance - (
            account.minimum_balance or Decimal("0.00")
        )

        # Create transaction
        transaction = Transaction(
            transaction_type="deposit",
            to_account_id=account.id,
            amount=request.amount,
            description=request.description or "Cash deposit",
            reference_number=generate_reference_number("DEP"),
            status="completed",
            to_balance_before=balance_before,
            to_balance_after=account.balance,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.TRANSACTION_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="transaction",
            resource_id=str(transaction.id),
            details={
                "type": "deposit",
                "amount": str(request.amount),
                "account": str(account.account_number),
                "reference": transaction.reference_number,
            },
        )

        return transaction

    @staticmethod
    def withdraw_money(
        db: Session, user_id: str, request: WithdrawRequest, ip_address: str
    ) -> Transaction:
        """Withdraw money from account.

        SECURITY: Validates account ownership, balance, minimum balance.

        Args:
            db: Database session
            user_id: User ID
            request: Withdrawal request data
            ip_address: Client IP address

        Returns:
            Transaction: Created transaction record

        Raises:
            ValueError: If validation fails
        """
        # Get account
        account = (
            db.query(Account)
            .filter(Account.id == request.account_id, Account.user_id == user_id)
            .first()
        )

        if not account:
            raise ValueError("Account not found or unauthorized")

        if account.status != "active":
            raise ValueError(f"Account is {account.status}")

        # Validate amount
        if request.amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        # Check sufficient balance
        min_balance = account.minimum_balance or Decimal("0.00")
        available = account.balance - min_balance

        if available < request.amount:
            raise ValueError(
                f"Insufficient balance. Available: ₹{available}, Required: ₹{request.amount}"
            )

        # Record balance before
        balance_before = account.balance

        # Update balance
        account.balance -= request.amount
        account.available_balance = account.balance - min_balance

        # Create transaction
        transaction = Transaction(
            transaction_type="withdrawal",
            from_account_id=account.id,
            amount=request.amount,
            description=request.description or "Cash withdrawal",
            reference_number=generate_reference_number("WDR"),
            status="completed",
            from_balance_before=balance_before,
            from_balance_after=account.balance,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.TRANSACTION_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="transaction",
            resource_id=str(transaction.id),
            details={
                "type": "withdrawal",
                "amount": str(request.amount),
                "account": str(account.account_number),
                "reference": transaction.reference_number,
            },
        )

        return transaction

    @staticmethod
    def get_transaction(db: Session, user_id: str, transaction_id: UUID) -> Transaction:
        """Get transaction details.

        SECURITY: Only returns transactions involving user's accounts.

        Args:
            db: Database session
            user_id: User ID
            transaction_id: Transaction ID

        Returns:
            Transaction: Transaction record

        Raises:
            ValueError: If transaction not found or unauthorized
        """
        transaction = (
            db.query(Transaction)
            .join(
                Account,
                or_(
                    Transaction.from_account_id == Account.id,
                    Transaction.to_account_id == Account.id,
                ),
            )
            .filter(Transaction.id == transaction_id, Account.user_id == user_id)
            .first()
        )

        if not transaction:
            raise ValueError("Transaction not found or unauthorized")

        return transaction

    @staticmethod
    def get_transaction_history(
        db: Session,
        user_id: str,
        filters: Optional[TransactionFilter] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Transaction]:
        """Get transaction history with filters.

        SECURITY: Only returns transactions involving user's accounts.

        Args:
            db: Database session
            user_id: User ID
            filters: Optional transaction filters
            skip: Pagination offset
            limit: Page size

        Returns:
            List of transactions
        """
        # Base query - only user's transactions
        query = (
            db.query(Transaction)
            .join(
                Account,
                or_(
                    Transaction.from_account_id == Account.id,
                    Transaction.to_account_id == Account.id,
                ),
            )
            .filter(Account.user_id == user_id)
        )

        # Apply filters if provided
        if filters:
            if filters.account_id:
                query = query.filter(
                    or_(
                        Transaction.from_account_id == filters.account_id,
                        Transaction.to_account_id == filters.account_id,
                    )
                )

            if filters.transaction_type:
                query = query.filter(Transaction.transaction_type == filters.transaction_type)

            if filters.start_date:
                query = query.filter(Transaction.created_at >= filters.start_date)

            if filters.end_date:
                # Include entire end date
                end_datetime = datetime.combine(
                    filters.end_date, datetime.max.time()
                )
                query = query.filter(Transaction.created_at <= end_datetime)

            if filters.min_amount:
                query = query.filter(Transaction.amount >= filters.min_amount)

            if filters.max_amount:
                query = query.filter(Transaction.amount <= filters.max_amount)

        # Order by date descending, paginate
        transactions = (
            query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
        )

        return transactions