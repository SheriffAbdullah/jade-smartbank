"""PyTest configuration and fixtures for testing.

SECURITY: Test fixtures use isolated test data and mock secrets.
"""
import os
from datetime import date
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator:
    """Setup test environment variables.

    SECURITY: Use test-only secrets, never production credentials.
    """
    # SECURITY: Test-only secret key
    os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production-12345678"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["RATE_LIMIT_ENABLED"] = "false"

    yield

    # Cleanup
    del os.environ["SECRET_KEY"]
    del os.environ["DATABASE_URL"]
    del os.environ["RATE_LIMIT_ENABLED"]


# Database fixtures
@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a test database session.

    SECURITY: Uses in-memory SQLite, isolated per test.
    """
    # Create test engine with in-memory SQLite
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override.

    SECURITY: Uses isolated test database.
    """

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# User fixtures
@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "phone": "+919876543210",
    }


@pytest.fixture
def sample_password() -> str:
    """Sample strong password for testing."""
    return "SecureP@ssw0rd123"


@pytest.fixture
def sample_weak_password() -> str:
    """Sample weak password for testing."""
    return "weak"


@pytest.fixture
def verified_user(test_db: Session, sample_password: str) -> User:
    """Create a verified user in the database.

    SECURITY: Uses hashed password.
    """
    user = User(
        email="verified@jadebank.com",
        phone="9876543210",
        password_hash=hash_password(sample_password),
        first_name="Verified",
        last_name="User",
        date_of_birth=date(1990, 1, 1),
        address_line1="123 Test Street",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400001",
        country="India",
        kyc_status="verified",
        is_verified=True,
        role="customer",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db: Session, sample_password: str) -> User:
    """Create an admin user in the database.

    SECURITY: Uses hashed password, admin role.
    """
    user = User(
        email="admin@jadebank.com",
        phone="9876543211",
        password_hash=hash_password(sample_password),
        first_name="Admin",
        last_name="User",
        date_of_birth=date(1985, 1, 1),
        address_line1="456 Admin Street",
        city="Delhi",
        state="Delhi",
        postal_code="110001",
        country="India",
        kyc_status="verified",
        is_verified=True,
        role="admin",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def unverified_user(test_db: Session, sample_password: str) -> User:
    """Create an unverified user (KYC pending).

    SECURITY: Uses hashed password.
    """
    user = User(
        email="unverified@jadebank.com",
        phone="9876543212",
        password_hash=hash_password(sample_password),
        first_name="Unverified",
        last_name="User",
        date_of_birth=date(1995, 1, 1),
        address_line1="789 Pending Street",
        city="Bangalore",
        state="Karnataka",
        postal_code="560001",
        country="India",
        kyc_status="pending",
        is_verified=False,
        role="customer",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# Account fixtures
@pytest.fixture
def savings_account(test_db: Session, verified_user: User) -> Account:
    """Create a savings account for verified user."""
    account = Account(
        user_id=verified_user.id,
        account_number="JADE12345678901234",
        account_type="savings",
        balance=50000.00,
        currency="INR",
        status="active",
        ifsc_code="JADE0000001",
        branch_name="Mumbai Main",
    )
    test_db.add(account)
    test_db.commit()
    test_db.refresh(account)
    return account


@pytest.fixture
def current_account(test_db: Session, verified_user: User) -> Account:
    """Create a current account for verified user."""
    account = Account(
        user_id=verified_user.id,
        account_number="JADE98765432109876",
        account_type="current",
        balance=100000.00,
        currency="INR",
        status="active",
        ifsc_code="JADE0000001",
        branch_name="Mumbai Main",
    )
    test_db.add(account)
    test_db.commit()
    test_db.refresh(account)
    return account


# Auth token fixtures
@pytest.fixture
def user_token(verified_user: User) -> str:
    """Create JWT access token for verified user.

    SECURITY: JWT token for authentication.
    """
    return create_access_token(data={"sub": str(verified_user.id), "role": "customer"})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create JWT access token for admin user.

    SECURITY: JWT token with admin role.
    """
    return create_access_token(data={"sub": str(admin_user.id), "role": "admin"})


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Create authorization headers for verified user.

    SECURITY: Bearer token authentication.
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth_headers(admin_token: str) -> dict:
    """Create authorization headers for admin user.

    SECURITY: Bearer token with admin privileges.
    """
    return {"Authorization": f"Bearer {admin_token}"}
