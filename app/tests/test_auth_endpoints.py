"""Integration tests for authentication endpoints.

SECURITY: Tests authentication, authorization, and KYC workflows.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.kyc_document import KYCDocument
from app.models.user import User

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@jadebank.com",
                "phone": "9876543213",
                "password": "SecureP@ss123",
                "first_name": "New",
                "last_name": "User",
                "date_of_birth": "1992-06-15",
                "gender": "male",
                "address_line1": "100 New Street",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postal_code": "600001",
                "country": "India",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@jadebank.com"
        assert data["phone"] == "9876543213"
        assert data["kyc_status"] == "pending"
        assert data["is_verified"] is False
        assert "user_id" in data

    def test_register_duplicate_email(self, client: TestClient, verified_user: User):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": verified_user.email,  # Duplicate
                "phone": "9876543214",
                "password": "SecureP@ss123",
                "first_name": "Duplicate",
                "last_name": "User",
                "date_of_birth": "1992-06-15",
                "address_line1": "101 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()["detail"].lower()

    def test_register_invalid_phone(self, client: TestClient):
        """Test registration with invalid phone number."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalidphone@jadebank.com",
                "phone": "123",  # Invalid
                "password": "SecureP@ss123",
                "first_name": "Invalid",
                "last_name": "Phone",
                "date_of_birth": "1992-06-15",
                "address_line1": "102 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@jadebank.com",
                "phone": "9876543215",
                "password": "weak",  # Too weak
                "first_name": "Weak",
                "last_name": "Pass",
                "date_of_birth": "1992-06-15",
                "address_line1": "103 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(
        self, client: TestClient, verified_user: User, sample_password: str
    ):
        """Test successful login with correct credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": verified_user.email, "password": sample_password},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert "expires_in" in data
        assert data["user"]["email"] == verified_user.email

    def test_login_wrong_password(self, client: TestClient, verified_user: User):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": verified_user.email, "password": "WrongP@ss123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "notexist@jadebank.com", "password": "SomeP@ss123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format."""
        response = client.post(
            "/api/v1/auth/login", json={"email": "notanemail", "password": "SomeP@ss123"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCurrentUserEndpoint:
    """Tests for GET /api/v1/auth/me."""

    def test_get_current_user_success(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test getting current user with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == verified_user.email
        assert data["phone"] == verified_user.phone
        assert data["kyc_status"] == "verified"

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token fails."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUploadKYCDocumentEndpoint:
    """Tests for POST /api/v1/auth/kyc/documents."""

    def test_upload_kyc_document_success(
        self,
        client: TestClient,
        test_db: Session,
        unverified_user: User,
        sample_password: str,
    ):
        """Test uploading KYC document successfully."""
        # Login as unverified user
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unverified_user.email, "password": sample_password},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload PAN document
        response = client.post(
            "/api/v1/auth/kyc/documents",
            json={
                "document_type": "pan",
                "document_number": "ABCDE1234F",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["document_type"] == "pan"
        assert data["document_number"] == "ABCDE1234F"
        assert data["is_verified"] is False

    def test_upload_kyc_document_no_auth(self, client: TestClient):
        """Test uploading KYC document without authentication fails."""
        response = client.post(
            "/api/v1/auth/kyc/documents",
            json={
                "document_type": "pan",
                "document_number": "ABCDE1234F",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_kyc_document_invalid_pan(
        self,
        client: TestClient,
        unverified_user: User,
        sample_password: str,
    ):
        """Test uploading KYC with invalid PAN format fails."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unverified_user.email, "password": sample_password},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload with invalid PAN
        response = client.post(
            "/api/v1/auth/kyc/documents",
            json={
                "document_type": "pan",
                "document_number": "INVALID123",  # Invalid format
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetKYCStatusEndpoint:
    """Tests for GET /api/v1/auth/kyc/status."""

    def test_get_kyc_status_success(
        self,
        client: TestClient,
        test_db: Session,
        verified_user: User,
        auth_headers: dict,
    ):
        """Test getting KYC status successfully."""
        # Add a KYC document
        doc = KYCDocument(
            user_id=verified_user.id,
            document_type="pan",
            document_number="ABCDE1234F",
            document_url="/uploads/kyc/pan_abcde1234f.pdf",
            is_verified=True,
        )
        test_db.add(doc)
        test_db.commit()

        response = client.get("/api/v1/auth/kyc/status", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["kyc_status"] == "verified"
        assert len(data["documents"]) == 1
        assert data["documents"][0]["document_type"] == "pan"

    def test_get_kyc_status_no_documents(
        self, client: TestClient, verified_user: User, auth_headers: dict
    ):
        """Test getting KYC status with no documents."""
        response = client.get("/api/v1/auth/kyc/status", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "kyc_status" in data
        assert "documents" in data

    def test_get_kyc_status_no_auth(self, client: TestClient):
        """Test getting KYC status without authentication fails."""
        response = client.get("/api/v1/auth/kyc/status")

        assert response.status_code == status.HTTP_403_FORBIDDEN