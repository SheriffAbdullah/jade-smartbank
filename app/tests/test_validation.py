"""Unit tests for validation utilities.

SECURITY: Tests cover input validation, sanitization, and edge cases.
Coverage target: 100%
"""
from decimal import Decimal

import pytest

from app.core.validation import (
    sanitize_string,
    validate_account_number,
    validate_amount,
    validate_email,
    validate_ifsc_code,
    validate_pan_number,
    validate_phone_number,
)


class TestStringValidation:
    """Test string sanitization."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = sanitize_string("  Hello World  ")

        assert result == "Hello World"

    def test_sanitize_string_removes_null_bytes(self):
        """Test removal of null bytes."""
        result = sanitize_string("Hello\x00World")

        assert result == "HelloWorld"
        assert "\x00" not in result

    def test_sanitize_string_removes_control_chars(self):
        """Test removal of control characters."""
        result = sanitize_string("Hello\x01\x02\x03World")

        assert result == "HelloWorld"

    def test_sanitize_string_keeps_newlines(self):
        """Test that newlines are preserved."""
        result = sanitize_string("Line1\nLine2")

        assert result == "Line1\nLine2"

    def test_sanitize_string_max_length(self):
        """Test max length enforcement."""
        long_string = "a" * 100

        with pytest.raises(ValueError, match="exceeds maximum length"):
            sanitize_string(long_string, max_length=50)

    def test_sanitize_string_non_string_input(self):
        """Test error on non-string input."""
        with pytest.raises(ValueError, match="must be a string"):
            sanitize_string(123)


class TestEmailValidation:
    """Test email validation."""

    def test_validate_email_valid(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.in",
            "user+tag@example.com",
            "user123@test-domain.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True, f"Failed for {email}"

    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com",
            "",
            None,
            123,
        ]

        for email in invalid_emails:
            assert validate_email(email) is False, f"Should fail for {email}"

    def test_validate_email_too_long(self):
        """Test email exceeding max length."""
        long_email = "a" * 250 + "@example.com"

        assert validate_email(long_email) is False


class TestPhoneValidation:
    """Test Indian phone number validation."""

    def test_validate_phone_valid(self):
        """Test valid Indian phone numbers."""
        valid_phones = [
            "9876543210",
            "8765432109",
            "7654321098",
            "6543210987",
            "+919876543210",
            "919876543210",
            "+91 98765 43210",
            "98765-43210",
        ]

        for phone in valid_phones:
            assert validate_phone_number(phone) is True, f"Failed for {phone}"

    def test_validate_phone_invalid(self):
        """Test invalid phone numbers."""
        invalid_phones = [
            "123",  # Too short
            "12345",  # Too short
            "1234567890",  # Doesn't start with 6-9
            "5987654321",  # Doesn't start with 6-9
            "abc1234567890",  # Contains letters
            "",
            None,
        ]

        for phone in invalid_phones:
            assert validate_phone_number(phone) is False, f"Should fail for {phone}"

    def test_validate_phone_wrong_length(self):
        """Test phone number with wrong length."""
        assert validate_phone_number("987654321") is False  # 9 digits
        assert validate_phone_number("98765432100") is False  # 11 digits


class TestAmountValidation:
    """Test monetary amount validation."""

    def test_validate_amount_valid_string(self):
        """Test valid amount as string."""
        is_valid, value = validate_amount("100.50")

        assert is_valid is True
        assert value == Decimal("100.50")

    def test_validate_amount_valid_float(self):
        """Test valid amount as float."""
        is_valid, value = validate_amount(100.50)

        assert is_valid is True
        assert value == Decimal("100.50")

    def test_validate_amount_valid_int(self):
        """Test valid amount as int."""
        is_valid, value = validate_amount(100)

        assert is_valid is True
        assert value == Decimal("100")

    def test_validate_amount_valid_decimal(self):
        """Test valid amount as Decimal."""
        is_valid, value = validate_amount(Decimal("100.50"))

        assert is_valid is True
        assert value == Decimal("100.50")

    def test_validate_amount_negative(self):
        """Test negative amount is invalid."""
        is_valid, value = validate_amount("-10.00")

        assert is_valid is False
        assert value is None

    def test_validate_amount_zero(self):
        """Test zero is invalid by default."""
        is_valid, value = validate_amount("0.00")

        assert is_valid is False

    def test_validate_amount_below_minimum(self):
        """Test amount below minimum."""
        is_valid, value = validate_amount("0.001", min_value=0.01)

        assert is_valid is False

    def test_validate_amount_too_many_decimals(self):
        """Test amount with too many decimal places."""
        is_valid, value = validate_amount("100.999")

        assert is_valid is False

    def test_validate_amount_overflow(self):
        """Test amount overflow."""
        is_valid, value = validate_amount("9999999999999999.99")

        assert is_valid is False

    def test_validate_amount_invalid_type(self):
        """Test invalid type."""
        is_valid, value = validate_amount(None)

        assert is_valid is False
        assert value is None

    def test_validate_amount_nan(self):
        """Test NaN is invalid."""
        is_valid, value = validate_amount(float('nan'))

        assert is_valid is False

    def test_validate_amount_infinity(self):
        """Test infinity is invalid."""
        is_valid, value = validate_amount(float('inf'))

        assert is_valid is False


class TestAccountNumberValidation:
    """Test Indian account number validation."""

    def test_validate_account_number_valid(self):
        """Test valid Indian account numbers."""
        valid_numbers = [
            "123456789",  # 9 digits
            "1234567890",  # 10 digits
            "12345678901234",  # 14 digits
            "123456789012345678",  # 18 digits
            "1234-5678-9012",  # With dashes
            "1234 5678 9012",  # With spaces
        ]

        for number in valid_numbers:
            assert validate_account_number(number) is True, f"Failed for {number}"

    def test_validate_account_number_invalid(self):
        """Test invalid account numbers."""
        invalid_numbers = [
            "12345678",  # Too short (8 digits)
            "1234567890123456789",  # Too long (19 digits)
            "12345ABC",  # Contains letters
            "",
            None,
        ]

        for number in invalid_numbers:
            assert validate_account_number(number) is False, f"Should fail for {number}"


class TestIFSCValidation:
    """Test IFSC code validation."""

    def test_validate_ifsc_valid(self):
        """Test valid IFSC codes."""
        valid_codes = [
            "SBIN0001234",
            "HDFC0001234",
            "ICIC0001234",
            "AXIS0001234",
            "sbin0001234",  # lowercase should work
            "SBIN 0001234",  # with space
        ]

        for code in valid_codes:
            assert validate_ifsc_code(code) is True, f"Failed for {code}"

    def test_validate_ifsc_invalid(self):
        """Test invalid IFSC codes."""
        invalid_codes = [
            "INVALID",  # Too short
            "SBIN1001234",  # 5th character not 0
            "SBI00001234",  # Only 3 letters
            "SBIN0001!@#",  # Special characters not allowed
            "123A0001234",  # First 4 not letters
            "SBIN00012",  # Too short (only 9 chars)
            "",
            None,
        ]

        for code in invalid_codes:
            assert validate_ifsc_code(code) is False, f"Should fail for {code}"


class TestPANValidation:
    """Test PAN number validation."""

    def test_validate_pan_valid(self):
        """Test valid PAN numbers."""
        valid_pans = [
            "ABCDE1234F",
            "AAAAA1111A",
            "ZZZZZ9999Z",
            "abcde1234f",  # lowercase should work
            "ABCDE 1234F",  # with spaces
        ]

        for pan in valid_pans:
            assert validate_pan_number(pan) is True, f"Failed for {pan}"

    def test_validate_pan_invalid(self):
        """Test invalid PAN numbers."""
        invalid_pans = [
            "INVALID",  # Wrong length
            "ABCD1234F",  # Only 4 letters at start
            "ABCDE12345",  # 5 digits
            "1BCDE1234F",  # Starts with digit
            "ABCDE1234",  # Missing last letter
            "",
            None,
        ]

        for pan in invalid_pans:
            assert validate_pan_number(pan) is False, f"Should fail for {pan}"
