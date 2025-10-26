"""Loan service for loan applications and EMI payments.

SECURITY: Validates KYC status, calculates accurate EMI, tracks payments.
"""
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditLogger
from app.models import Account, Loan, LoanEMIPayment, Transaction, User
from app.schemas.loan import (
    EMICalculationRequest,
    LoanApplicationRequest,
    LoanEMIPaymentRequest,
)
from app.utils import generate_reference_number
from app.utils.emi_calculator import calculate_emi


class LoanService:
    """Loan management service."""

    # Loan type configurations
    LOAN_CONFIGS = {
        "personal": {
            "max_amount": Decimal("500000.00"),
            "min_tenure": 6,
            "max_tenure": 60,
            "interest_rate": Decimal("12.5"),
        },
        "home": {
            "max_amount": Decimal("5000000.00"),
            "min_tenure": 60,
            "max_tenure": 360,
            "interest_rate": Decimal("8.5"),
        },
        "auto": {
            "max_amount": Decimal("1000000.00"),
            "min_tenure": 12,
            "max_tenure": 84,
            "interest_rate": Decimal("10.5"),
        },
        "education": {
            "max_amount": Decimal("2000000.00"),
            "min_tenure": 12,
            "max_tenure": 120,
            "interest_rate": Decimal("9.5"),
        },
    }

    @staticmethod
    def calculate_emi_for_loan(request: EMICalculationRequest) -> dict:
        """Calculate EMI for loan parameters.

        Uses the EMI utility function for accurate calculation.

        Args:
            request: EMI calculation parameters

        Returns:
            Dictionary with EMI details and amortization schedule

        Raises:
            ValueError: If loan type invalid or parameters out of range
        """
        # Validate loan type
        if request.loan_type not in LoanService.LOAN_CONFIGS:
            raise ValueError(
                f"Invalid loan type. Must be one of: {', '.join(LoanService.LOAN_CONFIGS.keys())}"
            )

        config = LoanService.LOAN_CONFIGS[request.loan_type]

        # Validate amount
        if request.principal_amount <= 0:
            raise ValueError("Loan amount must be positive")

        if request.principal_amount > config["max_amount"]:
            raise ValueError(
                f"Loan amount exceeds maximum of ₹{config['max_amount']} for {request.loan_type} loan"
            )

        # Validate tenure
        if not config["min_tenure"] <= request.tenure_months <= config["max_tenure"]:
            raise ValueError(
                f"Tenure must be between {config['min_tenure']} and {config['max_tenure']} months"
            )

        # Use provided interest rate or default
        interest_rate = request.interest_rate or config["interest_rate"]

        # Calculate EMI using utility
        emi, total_interest, total_payable, breakdown = calculate_emi(
            principal=request.principal_amount,
            annual_rate=interest_rate,
            tenure_months=request.tenure_months,
        )

        return {
            "loan_type": request.loan_type,
            "principal_amount": request.principal_amount,
            "interest_rate": interest_rate,
            "tenure_months": request.tenure_months,
            "emi_amount": emi,
            "total_interest": total_interest,
            "total_payable": total_payable,
            "amortization_schedule": breakdown,
        }

    @staticmethod
    def apply_for_loan(
        db: Session, user_id: str, request: LoanApplicationRequest, ip_address: str
    ) -> Loan:
        """Apply for a loan.

        SECURITY: Validates KYC status, calculates EMI, creates loan record.

        Args:
            db: Database session
            user_id: User ID
            request: Loan application data
            ip_address: Client IP address

        Returns:
            Loan: Created loan record

        Raises:
            ValueError: If validation fails
        """
        # Get user and validate KYC
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise ValueError("User not found")

        if not user.is_verified or user.kyc_status != "verified":
            raise ValueError("KYC verification required to apply for loan")

        # Validate loan type
        if request.loan_type not in LoanService.LOAN_CONFIGS:
            raise ValueError(
                f"Invalid loan type. Must be one of: {', '.join(LoanService.LOAN_CONFIGS.keys())}"
            )

        config = LoanService.LOAN_CONFIGS[request.loan_type]

        # Validate amount
        if request.principal_amount <= 0:
            raise ValueError("Loan amount must be positive")

        if request.principal_amount > config["max_amount"]:
            raise ValueError(
                f"Loan amount exceeds maximum of ₹{config['max_amount']} for {request.loan_type} loan"
            )

        # Validate tenure
        if not config["min_tenure"] <= request.tenure_months <= config["max_tenure"]:
            raise ValueError(
                f"Tenure must be between {config['min_tenure']} and {config['max_tenure']} months"
            )

        # Use provided interest rate or default
        interest_rate = request.interest_rate or config["interest_rate"]

        # Calculate EMI
        emi, total_interest, total_payable, _ = calculate_emi(
            principal=request.principal_amount,
            annual_rate=interest_rate,
            tenure_months=request.tenure_months,
        )

        # Validate disbursement account if provided
        disbursement_account = None
        if request.disbursement_account_id:
            disbursement_account = (
                db.query(Account)
                .filter(
                    Account.id == request.disbursement_account_id,
                    Account.user_id == user_id,
                )
                .first()
            )

            if not disbursement_account:
                raise ValueError("Disbursement account not found or unauthorized")

            if disbursement_account.status != "active":
                raise ValueError(f"Disbursement account is {disbursement_account.status}")

        # Create loan application
        loan = Loan(
            user_id=user_id,
            loan_type=request.loan_type,
            principal_amount=request.principal_amount,
            interest_rate=interest_rate,
            tenure_months=request.tenure_months,
            emi_amount=emi,
            total_interest=total_interest,
            total_payable=total_payable,
            outstanding_amount=request.principal_amount,
            disbursement_account_id=(
                disbursement_account.id if disbursement_account else None
            ),
            purpose=request.purpose,
            status="pending",  # Requires admin approval
        )

        db.add(loan)
        db.commit()
        db.refresh(loan)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="loan",
            resource_id=str(loan.id),
            details={
                "loan_type": request.loan_type,
                "principal": str(request.principal_amount),
                "tenure": request.tenure_months,
                "emi": str(emi),
            },
        )

        return loan

    @staticmethod
    def get_user_loans(db: Session, user_id: str) -> List[Loan]:
        """Get all loans for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of loans
        """
        return db.query(Loan).filter(Loan.user_id == user_id).all()

    @staticmethod
    def get_loan(db: Session, user_id: str, loan_id: UUID) -> Loan:
        """Get loan details.

        SECURITY: Only returns loans belonging to user.

        Args:
            db: Database session
            user_id: User ID
            loan_id: Loan ID

        Returns:
            Loan record

        Raises:
            ValueError: If loan not found or unauthorized
        """
        loan = (
            db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user_id).first()
        )

        if not loan:
            raise ValueError("Loan not found or unauthorized")

        return loan

    @staticmethod
    def get_emi_schedule(db: Session, user_id: str, loan_id: UUID) -> List[dict]:
        """Generate EMI payment schedule for loan.

        Args:
            db: Database session
            user_id: User ID
            loan_id: Loan ID

        Returns:
            List of EMI schedule items

        Raises:
            ValueError: If loan not found or unauthorized
        """
        loan = LoanService.get_loan(db, user_id, loan_id)

        # Get all payments made
        payments = (
            db.query(LoanEMIPayment)
            .filter(LoanEMIPayment.loan_id == loan_id)
            .order_by(LoanEMIPayment.emi_number)
            .all()
        )

        # Calculate full amortization schedule
        _, _, _, breakdown = calculate_emi(
            principal=loan.principal_amount,
            annual_rate=loan.interest_rate,
            tenure_months=loan.tenure_months,
        )

        # Merge with payment status
        schedule = []
        for item in breakdown:
            month = item["month"]
            payment = next((p for p in payments if p.emi_number == month), None)

            schedule.append(
                {
                    "emi_number": month,
                    "emi_amount": item["emi"],
                    "principal_component": item["principal"],
                    "interest_component": item["interest"],
                    "balance_after_emi": item["balance"],
                    "status": payment.status if payment else "pending",
                    "paid_on": payment.paid_at if payment else None,
                    "payment_reference": payment.payment_reference if payment else None,
                }
            )

        return schedule

    @staticmethod
    def pay_emi(
        db: Session, user_id: str, loan_id: UUID, request: LoanEMIPaymentRequest, ip_address: str
    ) -> LoanEMIPayment:
        """Pay EMI installment.

        SECURITY: Validates loan ownership, EMI amount, creates transaction.

        Args:
            db: Database session
            user_id: User ID
            loan_id: Loan ID
            request: EMI payment request
            ip_address: Client IP address

        Returns:
            LoanEMIPayment: Payment record

        Raises:
            ValueError: If validation fails
        """
        # Get loan
        loan = LoanService.get_loan(db, user_id, loan_id)

        # Validate loan status
        if loan.status != "active":
            raise ValueError(f"Cannot pay EMI for {loan.status} loan")

        # Get payment account
        account = (
            db.query(Account)
            .filter(Account.id == request.payment_account_id, Account.user_id == user_id)
            .first()
        )

        if not account:
            raise ValueError("Payment account not found or unauthorized")

        if account.status != "active":
            raise ValueError(f"Payment account is {account.status}")

        # Validate EMI number
        if request.emi_number < 1 or request.emi_number > loan.tenure_months:
            raise ValueError(
                f"Invalid EMI number. Must be between 1 and {loan.tenure_months}"
            )

        # Check if EMI already paid
        existing_payment = (
            db.query(LoanEMIPayment)
            .filter(
                LoanEMIPayment.loan_id == loan_id,
                LoanEMIPayment.emi_number == request.emi_number,
                LoanEMIPayment.status == "paid",
            )
            .first()
        )

        if existing_payment:
            raise ValueError(f"EMI #{request.emi_number} already paid")

        # Validate payment amount (allow slight variation for last EMI)
        is_last_emi = request.emi_number == loan.tenure_months
        expected_amount = loan.emi_amount
        tolerance = Decimal("1.00")  # ₹1 tolerance for rounding

        if not is_last_emi and abs(request.amount - expected_amount) > tolerance:
            raise ValueError(
                f"Invalid payment amount. Expected: ₹{expected_amount}, Received: ₹{request.amount}"
            )

        # Check sufficient balance
        min_balance = account.minimum_balance or Decimal("0.00")
        available = account.balance - min_balance

        if available < request.amount:
            raise ValueError(
                f"Insufficient balance. Available: ₹{available}, Required: ₹{request.amount}"
            )

        # Create transaction for EMI payment
        balance_before = account.balance
        account.balance -= request.amount
        account.available_balance = account.balance - min_balance

        transaction = Transaction(
            transaction_type="loan_payment",
            from_account_id=account.id,
            amount=request.amount,
            description=f"EMI payment for {loan.loan_type} loan - Month {request.emi_number}",
            reference_number=generate_reference_number("EMI"),
            status="completed",
            from_balance_before=balance_before,
            from_balance_after=account.balance,
        )

        db.add(transaction)

        # Create EMI payment record
        emi_payment = LoanEMIPayment(
            loan_id=loan_id,
            emi_number=request.emi_number,
            amount_paid=request.amount,
            payment_reference=transaction.reference_number,
            paid_at=datetime.utcnow(),
            status="paid",
        )

        db.add(emi_payment)

        # Update loan outstanding amount
        loan.outstanding_amount -= request.amount
        loan.emis_paid += 1

        # Check if loan fully paid
        if loan.emis_paid == loan.tenure_months:
            loan.status = "closed"
            loan.closed_at = datetime.utcnow()

        db.commit()
        db.refresh(emi_payment)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.TRANSACTION_CREATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="emi_payment",
            resource_id=str(emi_payment.id),
            details={
                "loan_id": str(loan_id),
                "emi_number": request.emi_number,
                "amount": str(request.amount),
                "reference": transaction.reference_number,
            },
        )

        return emi_payment

    @staticmethod
    def approve_loan(
        db: Session, loan_id: UUID, admin_id: str, ip_address: str
    ) -> Loan:
        """Approve loan application (Admin only).

        SECURITY: Disburses loan amount to user's account, updates status.

        Args:
            db: Database session
            loan_id: Loan ID
            admin_id: Admin user ID
            ip_address: Client IP address

        Returns:
            Loan: Updated loan record

        Raises:
            ValueError: If loan not found or already processed
        """
        loan = db.query(Loan).filter(Loan.id == loan_id).first()

        if not loan:
            raise ValueError("Loan not found")

        if loan.status != "pending":
            raise ValueError(f"Loan is already {loan.status}")

        # Approve loan
        loan.status = "active"
        loan.approved_by = admin_id
        loan.approved_at = datetime.utcnow()

        # Disburse amount if disbursement account specified
        if loan.disbursement_account_id:
            account = (
                db.query(Account).filter(Account.id == loan.disbursement_account_id).first()
            )

            if account:
                balance_before = account.balance
                account.balance += loan.principal_amount
                account.available_balance = account.balance - (
                    account.minimum_balance or Decimal("0.00")
                )

                # Create disbursement transaction
                transaction = Transaction(
                    transaction_type="loan_disbursement",
                    to_account_id=account.id,
                    amount=loan.principal_amount,
                    description=f"Loan disbursement - {loan.loan_type}",
                    reference_number=generate_reference_number("LND"),
                    status="completed",
                    to_balance_before=balance_before,
                    to_balance_after=account.balance,
                )

                db.add(transaction)

        db.commit()
        db.refresh(loan)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_UPDATED,
            user_id=admin_id,
            ip_address=ip_address,
            resource_type="loan",
            resource_id=str(loan.id),
            details={
                "action": "approved",
                "user_id": str(loan.user_id),
                "amount": str(loan.principal_amount),
            },
        )

        return loan

    @staticmethod
    def reject_loan(
        db: Session, loan_id: UUID, admin_id: str, rejection_reason: str, ip_address: str
    ) -> Loan:
        """Reject loan application (Admin only).

        Args:
            db: Database session
            loan_id: Loan ID
            admin_id: Admin user ID
            rejection_reason: Reason for rejection
            ip_address: Client IP address

        Returns:
            Loan: Updated loan record

        Raises:
            ValueError: If loan not found or already processed
        """
        loan = db.query(Loan).filter(Loan.id == loan_id).first()

        if not loan:
            raise ValueError("Loan not found")

        if loan.status != "pending":
            raise ValueError(f"Loan is already {loan.status}")

        # Reject loan
        loan.status = "rejected"
        loan.approved_by = admin_id
        loan.approved_at = datetime.utcnow()

        db.commit()
        db.refresh(loan)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_UPDATED,
            user_id=admin_id,
            ip_address=ip_address,
            resource_type="loan",
            resource_id=str(loan.id),
            details={
                "action": "rejected",
                "user_id": str(loan.user_id),
                "reason": rejection_reason,
            },
        )

        return loan