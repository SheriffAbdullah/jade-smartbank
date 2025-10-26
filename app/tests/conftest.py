"""PyTest configuration and fixtures for testing.

SECURITY: Test fixtures use isolated test data and mock secrets.
"""
import os
from typing import Generator

import pytest


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


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "phone": "+919876543210"
    }


@pytest.fixture
def sample_password() -> str:
    """Sample strong password for testing."""
    return "SecureP@ssw0rd123"


@pytest.fixture
def sample_weak_password() -> str:
    """Sample weak password for testing."""
    return "weak"
