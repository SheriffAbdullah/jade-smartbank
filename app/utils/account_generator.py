"""Account number and reference number generators.

SECURITY: Generates unique account and transaction reference numbers.
"""
import random
import string
import uuid
from datetime import datetime


def generate_account_number() -> str:
    """Generate unique 18-digit account number.

    Format: JADE + 14 random digits

    Returns:
        str: Account number (18 characters)

    Example:
        >>> account_num = generate_account_number()
        >>> len(account_num)
        18
        >>> account_num.startswith('JADE')
        True
    """
    # JADE prefix + 14 digits
    digits = "".join(random.choices(string.digits, k=14))
    return f"JADE{digits}"


def generate_reference_number(prefix: str = "TXN") -> str:
    """Generate unique transaction reference number.

    Format: PREFIX + timestamp + random string

    Args:
        prefix: Prefix for reference number (TXN, DEP, WD, EMI, etc.)

    Returns:
        str: Reference number

    Example:
        >>> ref = generate_reference_number("TXN")
        >>> ref.startswith('TXN')
        True
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_str}"


def generate_uuid() -> str:
    """Generate UUID string.

    Returns:
        str: UUID string
    """
    return str(uuid.uuid4())