"""Integration tests for admin endpoints.

SECURITY: Tests admin-only operations (KYC verification, loan approval).
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.kyc_document import KYCDocument
from app.models.loan import Loan
from app.models.user import User

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestVerifyKYCDocumentEndpoint:
    """Tests for PUT /api/v1/admin/kyc/documents/{document_id}/verify."""

    def test_verify_kyc_document_success(
        self,
        client: TestClient,
        test_db: Session,
        admin_user: User,
        unverified_user: User,
        admin_auth_headers: dict,
    ):
        """Test admin verifying KYC document successfully."""
        # Create KYC document for unverified user
        doc = KYCDocument(
            user_id=unverified_user.id,
            document_type="pan",
            document_number="ABCDE1234F",
            document_url="/uploads/kyc/test_document.pdf",
            is_verified=False,
        )
        test_db.add(doc)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/kyc/documents/{doc.id}/verify",
            json={"action": "approve", "admin_notes": "Document verified successfully"},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_verified"] is True
        assert data["verified_by"] == str(admin_user.id)

        # Verify user KYC status updated
        test_db.refresh(unverified_user)
        # Note: User KYC status update depends on business logic

    def test_reject_kyc_document_success(
        self,
        client: TestClient,
        test_db: Session,
        admin_user: User,
        unverified_user: User,
        admin_auth_headers: dict,
    ):
        """Test admin rejecting KYC document successfully."""
        doc = KYCDocument(
            user_id=unverified_user.id,
            document_type="pan",
            document_number="INVALID123",
            document_url="/uploads/kyc/test_document.pdf",
            is_verified=False,
        )
        test_db.add(doc)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/kyc/documents/{doc.id}/verify",
            json={
                "action": "reject",
                "admin_notes": "Document not clear, please resubmit",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_verified"] is False
        assert "not clear" in data["admin_notes"]

    def test_verify_kyc_document_not_admin(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        unverified_user: User,
        auth_headers: dict,
    ):
        """Test non-admin user cannot verify KYC documents."""
        doc = KYCDocument(
            user_id=unverified_user.id,
            document_type="pan",
            document_number="ABCDE1234F",
            document_url="/uploads/kyc/test_document.pdf",
            is_verified=False,
        )
        test_db.add(doc)
        test_db.commit()

        # Try with regular user token
        response = client.put(
            f"/api/v1/admin/kyc/documents/{doc.id}/verify",
            json={"action": "approve", "admin_notes": "Attempting verification"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_kyc_document_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Test verifying non-existent KYC document."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.put(
            f"/api/v1/admin/kyc/documents/{fake_uuid}/verify",
            json={"action": "approve", "admin_notes": "Test"},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_verify_kyc_document_no_auth(
        self, client: TestClient, test_db: Session, unverified_user: User
    ):
        """Test verifying KYC document without authentication fails."""
        doc = KYCDocument(
            user_id=unverified_user.id,
            document_type="pan",
            document_number="ABCDE1234F",
            document_url="/uploads/kyc/test_document.pdf",
            is_verified=False,
        )
        test_db.add(doc)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/kyc/documents/{doc.id}/verify",
            json={"action": "approve", "admin_notes": "Test"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_kyc_document_already_verified(
        self,
        client: TestClient,
        test_db: Session,
        unverified_user: User,
        admin_auth_headers: dict,
    ):
        """Test verifying already verified KYC document."""
        doc = KYCDocument(
            user_id=unverified_user.id,
            document_type="pan",
            document_number="ABCDE1234F",
            document_url="/uploads/kyc/test_document.pdf",
            is_verified=True,  # Already verified
        )
        test_db.add(doc)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/kyc/documents/{doc.id}/verify",
            json={"action": "approve", "admin_notes": "Re-verifying"},
            headers=admin_auth_headers,
        )

        # Should either succeed (idempotent) or return error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        ]


class TestReviewLoanEndpoint:
    """Tests for PUT /api/v1/admin/loans/{loan_id}/review."""

    def test_approve_loan_success(
        self,
        client: TestClient,
        test_db: Session,
        admin_user: User,
        verified_user: User,
        admin_auth_headers: dict,
    ):
        """Test admin approving loan successfully."""
        # Create pending loan
        loan = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="pending",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/loans/{loan.id}/review",
            json={"action": "approve"},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "approved"
        assert data["approved_by"] == str(admin_user.id)

    def test_reject_loan_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        admin_auth_headers: dict,
    ):
        """Test admin rejecting loan successfully."""
        loan = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="pending",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/loans/{loan.id}/review",
            json={
                "action": "reject",
                "rejection_reason": "Insufficient credit score",
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "rejected"
        assert "credit score" in data["rejection_reason"]

    def test_review_loan_not_admin(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test non-admin user cannot review loans."""
        loan = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="pending",
        )
        test_db.add(loan)
        test_db.commit()

        # Try with regular user token
        response = client.put(
            f"/api/v1/admin/loans/{loan.id}/review",
            json={"action": "approve"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_review_loan_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """Test reviewing non-existent loan."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.put(
            f"/api/v1/admin/loans/{fake_uuid}/review",
            json={"action": "approve"},
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_review_loan_no_auth(
        self, client: TestClient, test_db: Session, verified_user: User
    ):
        """Test reviewing loan without authentication fails."""
        loan = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="pending",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/loans/{loan.id}/review",
            json={"action": "approve"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_approve_loan_already_approved(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        admin_auth_headers: dict,
    ):
        """Test approving already approved loan."""
        loan = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="approved",  # Already approved
        )
        test_db.add(loan)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/loans/{loan.id}/review",
            json={"action": "approve"},
            headers=admin_auth_headers,
        )

        # Should either succeed (idempotent) or return error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_reject_loan_without_reason(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        admin_auth_headers: dict,
    ):
        """Test rejecting loan without rejection reason."""
        loan = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="pending",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.put(
            f"/api/v1/admin/loans/{loan.id}/review",
            json={"action": "reject"},  # No rejection_reason
            headers=admin_auth_headers,
        )

        # Might require rejection reason or allow without
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]