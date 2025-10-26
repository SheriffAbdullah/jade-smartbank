"""Unit tests for security utilities.

SECURITY: Tests cover password hashing, JWT operations, and edge cases.
Coverage target: 100%
"""
from datetime import datetime, timedelta

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_user_id_from_token,
    hash_password,
    validate_password_strength,
    verify_password,
    verify_token_type,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_hash(self, sample_password):
        """Test that password hashing produces a hash."""
        hashed = hash_password(sample_password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != sample_password
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self, sample_password):
        """Test that same password produces different hashes (salt)."""
        hash1 = hash_password(sample_password)
        hash2 = hash_password(sample_password)

        assert hash1 != hash2

    def test_verify_password_success(self, sample_password):
        """Test successful password verification."""
        hashed = hash_password(sample_password)

        assert verify_password(sample_password, hashed) is True

    def test_verify_password_failure(self, sample_password):
        """Test failed password verification with wrong password."""
        hashed = hash_password(sample_password)

        assert verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty string."""
        hashed = hash_password("test")

        assert verify_password("", hashed) is False


class TestPasswordValidation:
    """Test password strength validation."""

    def test_validate_strong_password(self, sample_password):
        """Test validation of strong password."""
        is_valid, errors = validate_password_strength(sample_password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_too_short_password(self):
        """Test validation fails for short password."""
        is_valid, errors = validate_password_strength("Short1!")

        assert is_valid is False
        assert any("at least 8 characters" in error for error in errors)

    def test_validate_no_uppercase(self):
        """Test validation fails without uppercase."""
        is_valid, errors = validate_password_strength("lowercase123!")

        assert is_valid is False
        assert any("uppercase" in error for error in errors)

    def test_validate_no_lowercase(self):
        """Test validation fails without lowercase."""
        is_valid, errors = validate_password_strength("UPPERCASE123!")

        assert is_valid is False
        assert any("lowercase" in error for error in errors)

    def test_validate_no_digit(self):
        """Test validation fails without digit."""
        is_valid, errors = validate_password_strength("NoDigits!@#")

        assert is_valid is False
        assert any("digit" in error for error in errors)

    def test_validate_no_special(self):
        """Test validation fails without special character."""
        is_valid, errors = validate_password_strength("NoSpecial123")

        assert is_valid is False
        assert any("special character" in error for error in errors)

    def test_validate_multiple_violations(self, sample_weak_password):
        """Test validation returns multiple errors."""
        is_valid, errors = validate_password_strength(sample_weak_password)

        assert is_valid is False
        assert len(errors) > 1


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self, sample_user_data):
        """Test access token creation."""
        token = create_access_token({"sub": sample_user_data["user_id"]})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, sample_user_data):
        """Test refresh token creation."""
        token = create_refresh_token({"sub": sample_user_data["user_id"]})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self, sample_user_data):
        """Test decoding valid token."""
        token = create_access_token({"sub": sample_user_data["user_id"]})
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == sample_user_data["user_id"]
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = decode_token("invalid.token.here")

        assert payload is None

    def test_decode_expired_token(self, sample_user_data):
        """Test decoding expired token."""
        # Create token that expires immediately
        token = create_access_token(
            {"sub": sample_user_data["user_id"]},
            expires_delta=timedelta(seconds=-1)
        )

        payload = decode_token(token)

        assert payload is None

    def test_verify_token_type_access(self, sample_user_data):
        """Test token type verification for access token."""
        token = create_access_token({"sub": sample_user_data["user_id"]})
        payload = decode_token(token)

        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False

    def test_verify_token_type_refresh(self, sample_user_data):
        """Test token type verification for refresh token."""
        token = create_refresh_token({"sub": sample_user_data["user_id"]})
        payload = decode_token(token)

        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False

    def test_extract_user_id_from_access_token(self, sample_user_data):
        """Test extracting user ID from access token."""
        token = create_access_token({"sub": sample_user_data["user_id"]})
        user_id = extract_user_id_from_token(token, token_type="access")

        assert user_id == sample_user_data["user_id"]

    def test_extract_user_id_from_refresh_token(self, sample_user_data):
        """Test extracting user ID from refresh token."""
        token = create_refresh_token({"sub": sample_user_data["user_id"]})
        user_id = extract_user_id_from_token(token, token_type="refresh")

        assert user_id == sample_user_data["user_id"]

    def test_extract_user_id_wrong_token_type(self, sample_user_data):
        """Test extracting user ID with wrong token type."""
        token = create_access_token({"sub": sample_user_data["user_id"]})
        user_id = extract_user_id_from_token(token, token_type="refresh")

        assert user_id is None

    def test_extract_user_id_invalid_token(self):
        """Test extracting user ID from invalid token."""
        user_id = extract_user_id_from_token("invalid.token", token_type="access")

        assert user_id is None

    def test_token_custom_expiration(self, sample_user_data):
        """Test token with custom expiration time."""
        custom_delta = timedelta(hours=2)
        token = create_access_token(
            {"sub": sample_user_data["user_id"]},
            expires_delta=custom_delta
        )
        payload = decode_token(token)

        assert payload is not None

        # Verify expiration is approximately 2 hours from now
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + custom_delta
        time_diff = abs((exp_time - expected_exp).total_seconds())

        assert time_diff < 5  # Within 5 seconds tolerance

    def test_token_includes_additional_data(self, sample_user_data):
        """Test token can include additional data."""
        additional_data = {
            "sub": sample_user_data["user_id"],
            "email": sample_user_data["email"],
            "role": "user"
        }
        token = create_access_token(additional_data)
        payload = decode_token(token)

        assert payload["email"] == sample_user_data["email"]
        assert payload["role"] == "user"
