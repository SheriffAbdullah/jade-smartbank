"""Account service for bank account management.

SECURITY: Account creation, balance management, and statement generation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditLogger
from app.models import Account, Transaction, User
from app.schemas.account import AccountCreate
from app.utils import generate_account_number


class AccountService:
    """Bank account management service."""

    # Account type defaults
    ACCOUNT_DEFAULTS = {
        "savings": {
            "min_balance": Decimal("1000.00"),
            "daily_limit": Decimal("100000.00"),
            "min_deposit": Decimal("500.00"),
        },
        "current": {
            "min_balance": Decimal("5000.00"),
            "daily_limit": Decimal("500000.00"),
            "min_deposit": Decimal("5000.00"),
        },
        "fd": {
            "min_balance": Decimal("0.00"),
            "daily_limit": Decimal("0.00"),
            "min_deposit": Decimal("10000.00"),
        },
    }

    @staticmethod
    def create_account(
        db: Session, user_id: str, request: AccountCreate, ip_address: str
    ) -> Account:
        """Create a new bank account.

        SECURITY: Validates KYC status, initial deposit, creates account with unique number.

        Args:
            db: Database session
            user_id: User ID
            request: Account creation request
            ip_address: Client IP address

        Returns:
            Account: Created account

        Raises:
            ValueError: If KYC not verified or invalid deposit
        """
        # Check KYC status
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.kyc_status != "verified":
            raise ValueError("KYC verification required to create account")

        # Get defaults for account type
        defaults = AccountService.ACCOUNT_DEFAULTS[request.account_type]

        # Validate minimum deposit
        if request.initial_deposit < defaults["min_deposit"]:
            raise ValueError(
                f"Minimum initial deposit for {request.account_type} account is ₹{defaults['min_deposit']}"
            )

        # Generate unique account number
        account_number = generate_account_number()

        # Create account
        account = Account(
            user_id=user_id,
            account_number=account_number,
            account_type=request.account_type,
            balance=request.initial_deposit,
            available_balance=request.initial_deposit,
            daily_transfer_limit=defaults["daily_limit"],
            min_balance=defaults["min_balance"],
            interest_rate=request.interest_rate,
            maturity_date=request.maturity_date,
            is_active=True,
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="account",
            resource_id=account.id,
            details={
                "account_number": account_number,
                "account_type": request.account_type,
                "initial_deposit": float(request.initial_deposit),
            },
        )

        return account

    @staticmethod
    def get_user_accounts(db: Session, user_id: str) -> List[Account]:
        """Get all accounts for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of accounts
        """
        return db.query(Account).filter(Account.user_id == user_id).all()

    @staticmethod
    def get_account(db: Session, account_id: str, user_id: str) -> Account:
        """Get specific account.

        Args:
            db: Database session
            account_id: Account ID
            user_id: User ID (for authorization)

        Returns:
            Account: Account details

        Raises:
            ValueError: If account not found or unauthorized
        """
        account = (
            db.query(Account)
            .filter(and_(Account.id == account_id, Account.user_id == user_id))
            .first()
        )

        if not account:
            raise ValueError("Account not found or unauthorized")

        return account

    @staticmethod
    def get_account_statement(
        db: Session,
        account_id: str,
        user_id: str,
        start_date: date,
        end_date: date,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[Account, List[Transaction], int]:
        """Get account statement with transactions.

        Args:
            db: Database session
            account_id: Account ID
            user_id: User ID
            start_date: Start date
            end_date: End date
            page: Page number
            limit: Results per page

        Returns:
            Tuple of (account, transactions, total_count)

        Raises:
            ValueError: If account not found
        """
        # Get account
        account = AccountService.get_account(db, account_id, user_id)

        # Get transactions
        query = db.query(Transaction).filter(
            and_(
                ((Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)),
                Transaction.created_at >= datetime.combine(start_date, datetime.min.time()),
                Transaction.created_at <= datetime.combine(end_date, datetime.max.time()),
            )
        ).order_by(Transaction.created_at.desc())

        total = query.count()
        transactions = query.offset((page - 1) * limit).limit(limit).all()

        return account, transactions, total