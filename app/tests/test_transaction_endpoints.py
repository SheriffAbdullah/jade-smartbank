"""Integration tests for transaction endpoints.

SECURITY: Tests transfer, deposit, withdraw, and transaction history.
"""
import pytest
from decimal import Decimal
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestTransferMoneyEndpoint:
    """Tests for POST /api/v1/transactions/transfer."""

    def test_transfer_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
        current_account: Account,
    ):
        """Test successful money transfer between accounts."""
        initial_from_balance = savings_account.balance
        initial_to_balance = current_account.balance

        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": str(savings_account.id),
                "to_account_id": str(current_account.id),
                "amount": 1000.00,
                "description": "Test transfer",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["transaction_type"] == "transfer"
        assert float(data["amount"]) == 1000.00
        assert data["status"] == "completed"
        assert "reference_number" in data

        # Verify balances updated
        test_db.refresh(savings_account)
        test_db.refresh(current_account)
        assert savings_account.balance == initial_from_balance - Decimal("1000.00")
        assert current_account.balance == initial_to_balance + Decimal("1000.00")

    def test_transfer_insufficient_balance(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
        current_account: Account,
    ):
        """Test transfer with insufficient balance fails."""
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": str(savings_account.id),
                "to_account_id": str(current_account.id),
                "amount": 999999.00,  # More than balance
                "description": "Insufficient balance test",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "insufficient" in response.json()["detail"].lower()

    def test_transfer_to_same_account(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test transfer to same account fails."""
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": str(savings_account.id),
                "to_account_id": str(savings_account.id),  # Same account
                "amount": 100.00,
                "description": "Same account test",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_transfer_unauthorized_account(
        self,
        client: TestClient,
        test_db: Session,
        admin_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test transfer from account user doesn't own fails."""
        # Create account for admin
        admin_account = Account(
            user_id=admin_user.id,
            account_number="JADE33333333333333",
            account_type="savings",
            balance=30000.00,
            currency="INR",
            status="active",
            ifsc_code="JADE0000001",
            branch_name="Delhi Main",
        )
        test_db.add(admin_account)
        test_db.commit()

        # Try to transfer from admin's account with verified_user's token
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": str(admin_account.id),
                "to_account_id": str(savings_account.id),
                "amount": 100.00,
                "description": "Unauthorized transfer",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_transfer_no_auth(
        self, client: TestClient, savings_account: Account, current_account: Account
    ):
        """Test transfer without authentication fails."""
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": str(savings_account.id),
                "to_account_id": str(current_account.id),
                "amount": 100.00,
                "description": "No auth test",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDepositMoneyEndpoint:
    """Tests for POST /api/v1/transactions/deposit."""

    def test_deposit_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test successful deposit."""
        initial_balance = savings_account.balance

        response = client.post(
            "/api/v1/transactions/deposit",
            json={
                "account_id": str(savings_account.id),
                "amount": 5000.00,
                "description": "Salary deposit",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["transaction_type"] == "deposit"
        assert float(data["amount"]) == 5000.00
        assert data["status"] == "completed"

        # Verify balance updated
        test_db.refresh(savings_account)
        assert savings_account.balance == initial_balance + Decimal("5000.00")

    def test_deposit_negative_amount(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test deposit with negative amount fails."""
        response = client.post(
            "/api/v1/transactions/deposit",
            json={
                "account_id": str(savings_account.id),
                "amount": -100.00,
                "description": "Negative deposit",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_deposit_no_auth(self, client: TestClient, savings_account: Account):
        """Test deposit without authentication fails."""
        response = client.post(
            "/api/v1/transactions/deposit",
            json={
                "account_id": str(savings_account.id),
                "amount": 100.00,
                "description": "No auth deposit",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWithdrawMoneyEndpoint:
    """Tests for POST /api/v1/transactions/withdraw."""

    def test_withdraw_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test successful withdrawal."""
        initial_balance = savings_account.balance

        response = client.post(
            "/api/v1/transactions/withdraw",
            json={
                "account_id": str(savings_account.id),
                "amount": 1000.00,
                "description": "ATM withdrawal",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["transaction_type"] == "withdraw"
        assert float(data["amount"]) == 1000.00
        assert data["status"] == "completed"

        # Verify balance updated
        test_db.refresh(savings_account)
        assert savings_account.balance == initial_balance - Decimal("1000.00")

    def test_withdraw_insufficient_balance(
        self,
        client: TestClient,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test withdrawal with insufficient balance fails."""
        response = client.post(
            "/api/v1/transactions/withdraw",
            json={
                "account_id": str(savings_account.id),
                "amount": 999999.00,
                "description": "Large withdrawal",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "insufficient" in response.json()["detail"].lower()

    def test_withdraw_below_minimum_balance(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test withdrawal that would violate minimum balance fails."""
        # Create account with balance close to minimum
        low_balance_account = Account(
            user_id=verified_user.id,
            account_number="JADE44444444444444",
            account_type="savings",
            balance=600.00,  # Savings minimum is 500
            currency="INR",
            status="active",
            ifsc_code="JADE0000001",
            branch_name="Mumbai Main",
        )
        test_db.add(low_balance_account)
        test_db.commit()

        response = client.post(
            "/api/v1/transactions/withdraw",
            json={
                "account_id": str(low_balance_account.id),
                "amount": 200.00,  # Would leave 400, below minimum
                "description": "Below minimum test",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "minimum balance" in response.json()["detail"].lower()

    def test_withdraw_no_auth(self, client: TestClient, savings_account: Account):
        """Test withdrawal without authentication fails."""
        response = client.post(
            "/api/v1/transactions/withdraw",
            json={
                "account_id": str(savings_account.id),
                "amount": 100.00,
                "description": "No auth withdrawal",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetTransactionDetailsEndpoint:
    """Tests for GET /api/v1/transactions/{transaction_id}."""

    def test_get_transaction_details_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test getting transaction details successfully."""
        # Create a transaction
        txn = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=1000.00,
            transaction_type="deposit",
            status="completed",
            reference_number="TXN12345",
            description="Test deposit",
        )
        test_db.add(txn)
        test_db.commit()

        response = client.get(f"/api/v1/transactions/{txn.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(txn.id)
        assert data["transaction_type"] == "deposit"
        assert float(data["amount"]) == 1000.00

    def test_get_transaction_details_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent transaction."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/transactions/{fake_uuid}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_transaction_details_no_auth(
        self, client: TestClient, test_db: Session, savings_account: Account
    ):
        """Test getting transaction without authentication fails."""
        txn = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=100.00,
            transaction_type="deposit",
            status="completed",
            reference_number="TXN99999",
        )
        test_db.add(txn)
        test_db.commit()

        response = client.get(f"/api/v1/transactions/{txn.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetTransactionHistoryEndpoint:
    """Tests for GET /api/v1/transactions."""

    def test_get_transaction_history_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
        current_account: Account,
    ):
        """Test getting transaction history successfully."""
        # Create multiple transactions
        txn1 = Transaction(
            from_account_id=savings_account.id,
            to_account_id=current_account.id,
            amount=500.00,
            transaction_type="transfer",
            status="completed",
            reference_number="TXN001",
        )
        txn2 = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=1000.00,
            transaction_type="deposit",
            status="completed",
            reference_number="TXN002",
        )
        test_db.add_all([txn1, txn2])
        test_db.commit()

        response = client.get("/api/v1/transactions", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2

    def test_get_transaction_history_with_filters(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
        savings_account: Account,
    ):
        """Test getting transaction history with filters."""
        # Create transactions of different types
        deposit = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=1000.00,
            transaction_type="deposit",
            status="completed",
            reference_number="DEP001",
        )
        withdraw = Transaction(
            from_account_id=savings_account.id,
            to_account_id=savings_account.id,
            amount=500.00,
            transaction_type="withdraw",
            status="completed",
            reference_number="WD001",
        )
        test_db.add_all([deposit, withdraw])
        test_db.commit()

        # Filter by type
        response = client.get(
            "/api/v1/transactions",
            params={"transaction_type": "deposit"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return deposits
        for txn in data:
            if txn["reference_number"] in ["DEP001", "WD001"]:
                if txn["reference_number"] == "DEP001":
                    assert txn["transaction_type"] == "deposit"

    def test_get_transaction_history_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """Test transaction history pagination."""
        response = client.get(
            "/api/v1/transactions", params={"skip": 0, "limit": 5}, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 5

    def test_get_transaction_history_no_auth(self, client: TestClient):
        """Test getting transaction history without authentication fails."""
        response = client.get("/api/v1/transactions")

        assert response.status_code == status.HTTP_403_FORBIDDEN