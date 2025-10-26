"""Loan management endpoints.

SECURITY: All routes require authentication. Admin routes require admin role.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, get_current_user, get_db, require_role
from app.models import User
from app.schemas.loan import (
    EMICalculationRequest,
    EMICalculationResponse,
    EMIScheduleResponse,
    LoanApplication,
    LoanEMIPaymentRequest,
    LoanEMIPaymentResponse,
    LoanResponse,
)
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/calculate-emi", response_model=EMICalculationResponse)
async def calculate_emi(
    data: EMICalculationRequest,
):
    """Calculate EMI for loan parameters.

    **No authentication required** - This is a calculator endpoint.

    **Business Rules**:
    - Validates loan type and parameters
    - Uses standard EMI formula: EMI = (P × r × (1+r)^n) / ((1+r)^n - 1)
    - Returns complete amortization schedule

    **Loan Types**:
    - `personal`: ₹5L max, 6-60 months, 12.5% interest
    - `home`: ₹50L max, 60-360 months, 8.5% interest
    - `auto`: ₹10L max, 12-84 months, 10.5% interest
    - `education`: ₹20L max, 12-120 months, 9.5% interest

    **Returns**: EMI amount, total interest, total payable, monthly breakdown
    """
    try:
        result = LoanService.calculate_emi_for_loan(data)

        return EMICalculationResponse(
            loan_type=result["loan_type"],
            principal_amount=result["principal_amount"],
            interest_rate=result["interest_rate"],
            tenure_months=result["tenure_months"],
            emi_amount=result["emi_amount"],
            total_interest=result["total_interest"],
            total_payable=result["total_payable"],
            amortization_schedule=result["amortization_schedule"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="EMI calculation failed",
        )


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_loan(
    request: Request,
    data: LoanApplication,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Apply for a loan.

    **SECURITY**: Requires authentication and verified KYC status.

    **Business Rules**:
    - User must have verified KYC
    - Loan amount and tenure must be within limits for loan type
    - EMI is automatically calculated
    - Loan requires admin approval before disbursement
    - Disbursement account must belong to user

    **Returns**: Loan application details with pending status
    """
    try:
        loan = LoanService.apply_for_loan(
            db=db, user_id=str(current_user.id), request=data, ip_address=ip_address
        )

        return LoanResponse(
            id=loan.id,
            user_id=loan.user_id,
            loan_type=loan.loan_type,
            principal_amount=loan.principal_amount,
            interest_rate=loan.interest_rate,
            tenure_months=loan.tenure_months,
            emi_amount=loan.emi_amount,
            total_interest=loan.total_interest,
            total_payable=loan.total_payable,
            outstanding_amount=loan.outstanding_amount,
            emis_paid=loan.emis_paid,
            disbursement_account_id=loan.disbursement_account_id,
            purpose=loan.purpose,
            status=loan.status,
            approved_by=loan.approved_by,
            approved_at=loan.approved_at,
            created_at=loan.created_at,
            updated_at=loan.updated_at,
            closed_at=loan.closed_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loan application failed",
        )


@router.get("", response_model=List[LoanResponse])
async def get_user_loans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all loans for authenticated user.

    **SECURITY**: Only returns loans belonging to authenticated user.

    **Returns**: List of all user's loans ordered by creation date
    """
    try:
        loans = LoanService.get_user_loans(db=db, user_id=str(current_user.id))

        return [
            LoanResponse(
                id=loan.id,
                user_id=loan.user_id,
                loan_type=loan.loan_type,
                principal_amount=loan.principal_amount,
                interest_rate=loan.interest_rate,
                tenure_months=loan.tenure_months,
                emi_amount=loan.emi_amount,
                total_interest=loan.total_interest,
                total_payable=loan.total_payable,
                outstanding_amount=loan.outstanding_amount,
                emis_paid=loan.emis_paid,
                disbursement_account_id=loan.disbursement_account_id,
                purpose=loan.purpose,
                status=loan.status,
                approved_by=loan.approved_by,
                approved_at=loan.approved_at,
                created_at=loan.created_at,
                updated_at=loan.updated_at,
                closed_at=loan.closed_at,
            )
            for loan in loans
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve loans",
        )


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan_details(
    loan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get loan details by ID.

    **SECURITY**: Only returns loans belonging to authenticated user.

    **Returns**: Complete loan details including payment status
    """
    try:
        loan = LoanService.get_loan(db=db, user_id=str(current_user.id), loan_id=loan_id)

        return LoanResponse(
            id=loan.id,
            user_id=loan.user_id,
            loan_type=loan.loan_type,
            principal_amount=loan.principal_amount,
            interest_rate=loan.interest_rate,
            tenure_months=loan.tenure_months,
            emi_amount=loan.emi_amount,
            total_interest=loan.total_interest,
            total_payable=loan.total_payable,
            outstanding_amount=loan.outstanding_amount,
            emis_paid=loan.emis_paid,
            disbursement_account_id=loan.disbursement_account_id,
            purpose=loan.purpose,
            status=loan.status,
            approved_by=loan.approved_by,
            approved_at=loan.approved_at,
            created_at=loan.created_at,
            updated_at=loan.updated_at,
            closed_at=loan.closed_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve loan details",
        )


@router.get("/{loan_id}/emi-schedule", response_model=EMIScheduleResponse)
async def get_emi_schedule(
    loan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get EMI payment schedule for loan.

    **SECURITY**: Only returns schedule for user's loans.

    **Returns**: Complete EMI schedule with payment status for each month
    - Shows principal and interest components
    - Marks paid vs pending EMIs
    - Includes payment references and dates
    """
    try:
        schedule = LoanService.get_emi_schedule(
            db=db, user_id=str(current_user.id), loan_id=loan_id
        )

        return EMIScheduleResponse(loan_id=loan_id, schedule=schedule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve EMI schedule",
        )


@router.post("/{loan_id}/pay-emi", response_model=LoanEMIPaymentResponse, status_code=status.HTTP_201_CREATED)
async def pay_emi(
    request: Request,
    loan_id: UUID,
    data: LoanEMIPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Pay EMI installment.

    **SECURITY**: Validates loan ownership, EMI amount, creates transaction.

    **Business Rules**:
    - Loan must be active
    - Payment amount must match EMI amount
    - Payment account must have sufficient balance
    - EMI must not already be paid
    - Updates outstanding amount and marks loan as closed if final EMI

    **Returns**: Payment confirmation with transaction reference
    """
    try:
        payment = LoanService.pay_emi(
            db=db,
            user_id=str(current_user.id),
            loan_id=loan_id,
            request=data,
            ip_address=ip_address,
        )

        return LoanEMIPaymentResponse(
            id=payment.id,
            loan_id=payment.loan_id,
            emi_number=payment.emi_number,
            amount_paid=payment.amount_paid,
            payment_reference=payment.payment_reference,
            paid_at=payment.paid_at,
            status=payment.status,
            message="EMI payment successful",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="EMI payment failed",
        )