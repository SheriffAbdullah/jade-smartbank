"""Admin endpoints for KYC verification and loan approval.

SECURITY: All routes require admin role.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, get_current_user, require_role
from app.db.base import get_db
from app.models import User
from app.schemas.kyc import KYCDocumentResponse, KYCVerificationRequest
from app.schemas.loan import LoanApprovalRequest, LoanResponse
from app.services.kyc_service import KYCService
from app.services.loan_service import LoanService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.put(
    "/kyc/documents/{document_id}/verify",
    response_model=KYCDocumentResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def verify_kyc_document(
    request: Request,
    document_id: UUID,
    data: KYCVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Verify or reject KYC document.

    **SECURITY**: Admin role required.

    **Business Rules**:
    - Updates document verification status
    - If 2+ documents verified, user KYC status becomes "verified"
    - Rejection reason required if rejecting
    - Audit logged

    **Returns**: Updated KYC document with verification details
    """
    try:
        document = KYCService.verify_document(
            db=db,
            document_id=str(document_id),
            admin_id=str(current_user.id),
            is_verified=data.is_verified,
            rejection_reason=data.rejection_reason,
            ip_address=ip_address,
        )

        return KYCDocumentResponse(
            id=document.id,
            user_id=document.user_id,
            document_type=document.document_type,
            document_number=document.document_number,
            document_url=document.document_url,
            is_verified=document.is_verified,
            verified_by=document.verified_by,
            verified_at=document.verified_at,
            rejection_reason=document.rejection_reason,
            uploaded_at=document.uploaded_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KYC verification failed",
        )


@router.put(
    "/loans/{loan_id}/review",
    response_model=LoanResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def review_loan(
    request: Request,
    loan_id: UUID,
    data: LoanApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
):
    """Approve or reject loan application.

    **SECURITY**: Admin role required.

    **Business Rules**:
    - Loan must be in pending status
    - If approved: Disburses amount to user's account (if specified)
    - If rejected: Requires rejection reason
    - Updates loan status and audit log

    **Returns**: Updated loan details with approval status
    """
    try:
        if data.action == "approve":
            loan = LoanService.approve_loan(
                db=db,
                loan_id=loan_id,
                admin_id=str(current_user.id),
                ip_address=ip_address,
            )
        elif data.action == "reject":
            if not data.rejection_reason:
                raise ValueError("Rejection reason is required")

            loan = LoanService.reject_loan(
                db=db,
                loan_id=loan_id,
                admin_id=str(current_user.id),
                rejection_reason=data.rejection_reason,
                ip_address=ip_address,
            )
        else:
            raise ValueError("Invalid action. Must be 'approve' or 'reject'")

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
            detail="Loan review failed",
        )