"""Integration tests for account endpoints.

SECURITY: Tests account creation, retrieval, and statement generation.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestCreateAccountEndpoint:
    """Tests for POST /api/v1/accounts."""

    def test_create_savings_account_success(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test creating a savings account successfully."""
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "initial_deposit": 1000.00},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["account_type"] == "savings"
        assert float(data["balance"]) == 1000.00
        assert data["is_active"] is True
        assert data["account_number"].startswith("JADE")
        assert len(data["account_number"]) == 18

    def test_create_current_account_success(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test creating a current account successfully."""
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "current", "initial_deposit": 5000.00},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["account_type"] == "current"
        assert float(data["balance"]) == 5000.00

    def test_create_account_below_minimum(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test creating account with below minimum deposit fails."""
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "initial_deposit": 100.00},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "minimum" in response.json()["detail"].lower()

    def test_create_account_unverified_kyc(
        self, client: TestClient, unverified_user: User, sample_password: str
    ):
        """Test creating account with unverified KYC fails."""
        # Login as unverified user
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unverified_user.email, "password": sample_password},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "initial_deposit": 1000.00},
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "kyc" in response.json()["detail"].lower()

    def test_create_account_no_auth(self, client: TestClient):
        """Test creating account without authentication fails."""
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "initial_deposit": 1000.00},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListAccountsEndpoint:
    """Tests for GET /api/v1/accounts."""

    def test_list_accounts_success(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
        current_account: Account,
    ):
        """Test listing user accounts successfully."""
        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        account_types = {acc["account_type"] for acc in data}
        assert "savings" in account_types
        assert "current" in account_types

    def test_list_accounts_empty(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test listing accounts when user has none."""
        response = client.get("/api/v1/accounts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_accounts_no_auth(self, client: TestClient):
        """Test listing accounts without authentication fails."""
        response = client.get("/api/v1/accounts")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetAccountDetailsEndpoint:
    """Tests for GET /api/v1/accounts/{account_id}."""

    def test_get_account_details_success(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test getting account details successfully."""
        response = client.get(
            f"/api/v1/accounts/{savings_account.id}", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(savings_account.id)
        assert data["account_type"] == "savings"
        assert float(data["balance"]) == 50000.00

    def test_get_account_details_not_found(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test getting non-existent account details."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/accounts/{fake_uuid}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_account_details_unauthorized_user(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        admin_user: User,
        auth_headers: dict,
        sample_password: str,
    ):
        """Test getting another user's account details fails."""
        # Create account for admin user
        from decimal import Decimal
        admin_account = Account(
            user_id=admin_user.id,
            account_number="JADE11111111111111",
            account_type="savings",
            balance=Decimal("10000.00"),
            available_balance=Decimal("10000.00"),
            is_active=True,
            ifsc_code="JADE0000001",
        )
        test_db.add(admin_account)
        test_db.commit()

        # Try to access admin's account with verified_user's token
        response = client.get(
            f"/api/v1/accounts/{admin_account.id}", headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_account_details_no_auth(
        self, client: TestClient, savings_account: Account
    ):
        """Test getting account details without authentication fails."""
        response = client.get(f"/api/v1/accounts/{savings_account.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetAccountStatementEndpoint:
    """Tests for GET /api/v1/accounts/{account_id}/statement."""

    def test_get_account_statement_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test getting account statement successfully."""
        # Create some transactions
        txn1 = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=1000.00,
            transaction_type="deposit",
            status="completed",
            reference_number="TXN001",
        )
        txn2 = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=500.00,
            transaction_type="withdraw",
            status="completed",
            reference_number="TXN002",
        )
        test_db.add_all([txn1, txn2])
        test_db.commit()

        response = client.get(
            f"/api/v1/accounts/{savings_account.id}/statement", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "account" in data
        assert "transactions" in data
        assert len(data["transactions"]) == 2

    def test_get_account_statement_with_date_filter(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test getting account statement with date filters."""
        response = client.get(
            f"/api/v1/accounts/{savings_account.id}/statement",
            params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "transactions" in data

    def test_get_account_statement_no_auth(
        self, client: TestClient, savings_account: Account
    ):
        """Test getting statement without authentication fails."""
        response = client.get(f"/api/v1/accounts/{savings_account.id}/statement")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_account_statement_wrong_user(
        self,
        client: TestClient,
        test_db: Session,
        admin_user: User,
        auth_headers: dict,
    ):
        """Test getting statement for another user's account fails."""
        # Create account for admin
        from decimal import Decimal
        admin_account = Account(
            user_id=admin_user.id,
            account_number="JADE22222222222222",
            account_type="savings",
            balance=Decimal("20000.00"),
            available_balance=Decimal("20000.00"),
            is_active=True,
            ifsc_code="JADE0000001",
        )
        test_db.add(admin_account)
        test_db.commit()

        # Try to access with verified_user's token
        response = client.get(
            f"/api/v1/accounts/{admin_account.id}/statement", headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN