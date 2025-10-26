"""Input validation and sanitization utilities.

SECURITY: All user inputs must be validated and sanitized before processing.
Prevent injection attacks, XSS, and invalid data.
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input by removing dangerous characters.

    SECURITY: Removes null bytes, control characters, and trims whitespace.
    Use max_length to prevent DoS via large inputs.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized string

    Raises:
        ValueError: If string exceeds max_length

    Example:
        >>> sanitize_string("  Hello\\x00World  ", max_length=50)
        'HelloWorld'
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Remove null bytes and control characters
    sanitized = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

    # Strip whitespace
    sanitized = sanitized.strip()

    # Check length
    if max_length and len(sanitized) > max_length:
        raise ValueError(f"String exceeds maximum length of {max_length}")

    return sanitized


def validate_email(email: str) -> bool:
    """Validate email address format.

    SECURITY: Basic format validation. Additional verification
    (like domain check or confirmation email) recommended.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid format, False otherwise

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 254


def validate_phone_number(phone: str) -> bool:
    """Validate Indian phone number format.

    SECURITY: Validates format only, not if number actually exists.
    Accepts 10-digit Indian mobile numbers with optional +91 country code.

    Args:
        phone: Phone number to validate

    Returns:
        bool: True if valid format, False otherwise

    Example:
        >>> validate_phone_number("9876543210")
        True
        >>> validate_phone_number("+919876543210")
        True
        >>> validate_phone_number("123")
        False
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

    # Handle +91 prefix for India
    if cleaned.startswith('+91'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]

    # Must be digits only
    if not cleaned.isdigit():
        return False

    # Indian mobile numbers are 10 digits starting with 6-9
    if len(cleaned) != 10:
        return False

    # First digit should be 6, 7, 8, or 9
    return cleaned[0] in '6789'


def validate_amount(amount: str | float | Decimal, min_value: float = 0.01) -> tuple[bool, Optional[Decimal]]:
    """Validate monetary amount.

    SECURITY: Prevents negative amounts, overflow, and precision issues.
    Returns Decimal for accurate financial calculations.

    Args:
        amount: Amount to validate
        min_value: Minimum allowed value

    Returns:
        tuple[bool, Optional[Decimal]]: (is_valid, decimal_value)

    Example:
        >>> valid, value = validate_amount("100.50")
        >>> valid
        True
        >>> value
        Decimal('100.50')
    """
    try:
        # Convert to Decimal for precision
        if isinstance(amount, str):
            decimal_amount = Decimal(amount)
        elif isinstance(amount, (int, float)):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            return False, None

        # Check for NaN or Infinity
        if not decimal_amount.is_finite():
            return False, None

        # Check minimum value
        if decimal_amount < Decimal(str(min_value)):
            return False, None

        # Check reasonable maximum (prevent overflow)
        max_value = Decimal("999999999999.99")
        if decimal_amount > max_value:
            return False, None

        # Limit to 2 decimal places for currency
        if decimal_amount.as_tuple().exponent < -2:
            return False, None

        return True, decimal_amount

    except (InvalidOperation, ValueError, TypeError):
        return False, None


def validate_account_number(account_number: str) -> bool:
    """Validate Indian bank account number format.

    SECURITY: Validates format and length, not actual existence.
    Indian account numbers are typically 9-18 digits.

    Args:
        account_number: Account number to validate

    Returns:
        bool: True if valid format, False otherwise

    Example:
        >>> validate_account_number("1234567890123")
        True
        >>> validate_account_number("12AB")
        False
    """
    if not account_number or not isinstance(account_number, str):
        return False

    # Remove spaces and dashes
    cleaned = account_number.replace(" ", "").replace("-", "")

    # Must be digits only
    if not cleaned.isdigit():
        return False

    # Indian account numbers are typically 9-18 digits
    return 9 <= len(cleaned) <= 18


def validate_ifsc_code(ifsc_code: str) -> bool:
    """Validate Indian IFSC (Indian Financial System Code).

    SECURITY: Validates format only, not actual existence.
    Format: 4 letters (bank code) + 0 + 6 alphanumeric (branch code)

    Args:
        ifsc_code: 11-character IFSC code

    Returns:
        bool: True if valid format, False otherwise

    Example:
        >>> validate_ifsc_code("SBIN0001234")
        True
        >>> validate_ifsc_code("INVALID")
        False
    """
    if not ifsc_code or not isinstance(ifsc_code, str):
        return False

    # Remove spaces and convert to uppercase
    cleaned = ifsc_code.replace(" ", "").upper()

    # Must be exactly 11 characters
    if len(cleaned) != 11:
        return False

    # Pattern: 4 letters + 0 + 6 alphanumeric
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    return bool(re.match(pattern, cleaned))


def validate_pan_number(pan: str) -> bool:
    """Validate Indian PAN (Permanent Account Number).

    SECURITY: Validates format only, not actual existence.
    Format: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)

    Args:
        pan: 10-character PAN number

    Returns:
        bool: True if valid format, False otherwise

    Example:
        >>> validate_pan_number("ABCDE1234F")
        True
        >>> validate_pan_number("INVALID")
        False
    """
    if not pan or not isinstance(pan, str):
        return False

    # Remove spaces and convert to uppercase
    cleaned = pan.replace(" ", "").upper()

    # Must be exactly 10 characters
    if len(cleaned) != 10:
        return False

    # Pattern: 5 letters + 4 digits + 1 letter
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    return bool(re.match(pattern, cleaned))
