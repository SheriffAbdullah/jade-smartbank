"""Integration tests for loan endpoints.

SECURITY: Tests loan application, EMI calculation, and payment processing.
"""
import pytest
from decimal import Decimal
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.loan import Loan
from app.models.user import User

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestCalculateEMIEndpoint:
    """Tests for POST /api/v1/loans/calculate-emi (public endpoint)."""

    def test_calculate_emi_success(self, client: TestClient):
        """Test EMI calculation without authentication (public endpoint)."""
        response = client.post(
            "/api/v1/loans/calculate-emi",
            json={
                "loan_type": "personal",
                "principal_amount": 100000.00,
                "tenure_months": 12,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "emi_amount" in data
        assert "total_payable" in data
        assert "total_interest" in data
        assert "amortization_schedule" in data
        assert float(data["principal_amount"]) == 100000.00
        assert data["tenure_months"] == 12

    def test_calculate_emi_with_custom_rate(self, client: TestClient):
        """Test EMI calculation with custom interest rate."""
        response = client.post(
            "/api/v1/loans/calculate-emi",
            json={
                "loan_type": "personal",
                "principal_amount": 50000.00,
                "interest_rate": 10.5,
                "tenure_months": 24,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["interest_rate"]) == 10.5

    def test_calculate_emi_invalid_loan_type(self, client: TestClient):
        """Test EMI calculation with invalid loan type."""
        response = client.post(
            "/api/v1/loans/calculate-emi",
            json={
                "loan_type": "invalid_type",
                "principal_amount": 100000.00,
                "tenure_months": 12,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_calculate_emi_zero_amount(self, client: TestClient):
        """Test EMI calculation with zero amount fails."""
        response = client.post(
            "/api/v1/loans/calculate-emi",
            json={"loan_type": "personal", "principal_amount": 0, "tenure_months": 12},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestApplyForLoanEndpoint:
    """Tests for POST /api/v1/loans."""

    def test_apply_for_loan_success(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test successful loan application."""
        response = client.post(
            "/api/v1/loans",
            json={
                "loan_type": "personal",
                "principal_amount": 50000.00,
                "tenure_months": 12,
                "purpose": "Home renovation",
                "disbursement_account_id": str(savings_account.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["loan_type"] == "personal"
        assert float(data["principal_amount"]) == 50000.00
        assert data["tenure_months"] == 12
        assert data["status"] == "pending"
        assert "emi_amount" in data
        assert "total_payable" in data

    def test_apply_for_loan_unverified_kyc(
        self, client: TestClient, unverified_user: User, sample_password: str
    ):
        """Test loan application with unverified KYC fails."""
        # Login as unverified user
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unverified_user.email, "password": sample_password},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/v1/loans",
            json={
                "loan_type": "personal",
                "principal_amount": 50000.00,
                "tenure_months": 12,
                "purpose": "Test loan",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "kyc" in response.json()["detail"].lower()

    def test_apply_for_loan_exceeds_maximum(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test loan application exceeding maximum amount fails."""
        response = client.post(
            "/api/v1/loans",
            json={
                "loan_type": "personal",
                "principal_amount": 9999999.00,  # Exceeds personal loan max
                "tenure_months": 12,
                "purpose": "Too large",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "maximum" in response.json()["detail"].lower()

    def test_apply_for_loan_invalid_tenure(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test loan application with invalid tenure fails."""
        response = client.post(
            "/api/v1/loans",
            json={
                "loan_type": "personal",
                "principal_amount": 50000.00,
                "tenure_months": 120,  # Exceeds personal loan max tenure
                "purpose": "Long tenure",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_for_loan_no_auth(self, client: TestClient):
        """Test loan application without authentication fails."""
        response = client.post(
            "/api/v1/loans",
            json={
                "loan_type": "personal",
                "principal_amount": 50000.00,
                "tenure_months": 12,
                "purpose": "No auth",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUserLoansEndpoint:
    """Tests for GET /api/v1/loans."""

    def test_get_user_loans_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test getting user's loans successfully."""
        # Create test loans
        loan1 = Loan(
            user_id=verified_user.id,
            loan_type="personal",
            principal_amount=50000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=4454.33,
            total_interest=3451.96,
            total_payable=53451.96,
            outstanding_amount=53451.96,
            status="approved",
        )
        loan2 = Loan(
            user_id=verified_user.id,
            loan_type="auto",
            principal_amount=200000.00,
            interest_rate=10.5,
            tenure_months=36,
            emi_amount=6496.35,
            total_interest=33868.60,
            total_payable=233868.60,
            outstanding_amount=233868.60,
            status="pending",
        )
        test_db.add_all([loan1, loan2])
        test_db.commit()

        response = client.get("/api/v1/loans", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        loan_types = {loan["loan_type"] for loan in data}
        assert "personal" in loan_types
        assert "auto" in loan_types

    def test_get_user_loans_empty(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test getting loans when user has none."""
        response = client.get("/api/v1/loans", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_user_loans_no_auth(self, client: TestClient):
        """Test getting loans without authentication fails."""
        response = client.get("/api/v1/loans")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetLoanDetailsEndpoint:
    """Tests for GET /api/v1/loans/{loan_id}."""

    def test_get_loan_details_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test getting loan details successfully."""
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
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.get(f"/api/v1/loans/{loan.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(loan.id)
        assert data["loan_type"] == "personal"
        assert float(data["principal_amount"]) == 50000.00

    def test_get_loan_details_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent loan details."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/loans/{fake_uuid}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_loan_details_wrong_user(
        self,
        client: TestClient,
        test_db: Session,
        admin_user: User,
        auth_headers: dict,
    ):
        """Test getting another user's loan details fails."""
        # Create loan for admin
        admin_loan = Loan(
            user_id=admin_user.id,
            loan_type="personal",
            principal_amount=30000.00,
            interest_rate=12.5,
            tenure_months=12,
            emi_amount=2672.60,
            total_interest=2071.20,
            total_payable=32071.20,
            outstanding_amount=32071.20,
            status="approved",
        )
        test_db.add(admin_loan)
        test_db.commit()

        # Try to access with verified_user's token
        response = client.get(f"/api/v1/loans/{admin_loan.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_loan_details_no_auth(self, client: TestClient, test_db: Session, verified_user: User):
        """Test getting loan details without authentication fails."""
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
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.get(f"/api/v1/loans/{loan.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetEMIScheduleEndpoint:
    """Tests for GET /api/v1/loans/{loan_id}/emi-schedule."""

    def test_get_emi_schedule_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test getting EMI schedule successfully."""
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
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.get(
            f"/api/v1/loans/{loan.id}/emi-schedule", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "loan_id" in data
        assert "schedule" in data
        assert len(data["schedule"]) == 12  # 12 months
        # Verify schedule structure
        first_emi = data["schedule"][0]
        assert "emi_number" in first_emi
        assert "emi_amount" in first_emi
        assert "principal_component" in first_emi
        assert "interest_component" in first_emi

    def test_get_emi_schedule_no_auth(self, client: TestClient, test_db: Session, verified_user: User):
        """Test getting EMI schedule without authentication fails."""
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
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.get(f"/api/v1/loans/{loan.id}/emi-schedule")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPayEMIEndpoint:
    """Tests for POST /api/v1/loans/{loan_id}/pay-emi."""

    def test_pay_emi_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test paying EMI successfully."""
        # Create approved loan
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
            emis_paid=0,
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        initial_balance = savings_account.balance

        response = client.post(
            f"/api/v1/loans/{loan.id}/pay-emi",
            json={
                "payment_account_id": str(savings_account.id),
                "emi_number": 1,
                "amount": 4454.33,
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["loan_id"] == str(loan.id)
        assert data["emi_number"] == 1
        assert float(data["amount_paid"]) == 4454.33
        assert data["status"] == "completed"

        # Verify balance deducted
        test_db.refresh(savings_account)
        assert savings_account.balance == initial_balance - Decimal("4454.33")

    def test_pay_emi_insufficient_balance(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test paying EMI with insufficient balance fails."""
        # Create account with low balance
        low_balance_account = Account(
            user_id=verified_user.id,
            account_number="JADE55555555555555",
            account_type="savings",
            balance=1000.00,
            currency="INR",
            status="active",
            ifsc_code="JADE0000001",
            branch_name="Mumbai Main",
        )
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
            status="approved",
        )
        test_db.add_all([low_balance_account, loan])
        test_db.commit()

        response = client.post(
            f"/api/v1/loans/{loan.id}/pay-emi",
            json={
                "payment_account_id": str(low_balance_account.id),
                "emi_number": 1,
                "amount": 4454.33,
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "insufficient" in response.json()["detail"].lower()

    def test_pay_emi_wrong_amount(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test paying EMI with wrong amount fails."""
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
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.post(
            f"/api/v1/loans/{loan.id}/pay-emi",
            json={
                "payment_account_id": str(savings_account.id),
                "emi_number": 1,
                "amount": 1000.00,  # Wrong amount
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pay_emi_pending_loan(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test paying EMI for pending (not approved) loan fails."""
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
            status="pending",  # Not approved
        )
        test_db.add(loan)
        test_db.commit()

        response = client.post(
            f"/api/v1/loans/{loan.id}/pay-emi",
            json={
                "payment_account_id": str(savings_account.id),
                "emi_number": 1,
                "amount": 4454.33,
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "approved" in response.json()["detail"].lower()

    def test_pay_emi_no_auth(self, client: TestClient, test_db: Session, verified_user: User):
        """Test paying EMI without authentication fails."""
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
            status="approved",
        )
        test_db.add(loan)
        test_db.commit()

        response = client.post(
            f"/api/v1/loans/{loan.id}/pay-emi",
            json={
                "payment_account_id": "some-account-id",
                "emi_number": 1,
                "amount": 4454.33,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED