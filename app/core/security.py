"""Security utilities for authentication and authorization.

SECURITY: This module handles password hashing, JWT token generation/validation,
and access control. All sensitive operations must be audited.
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# SECURITY: Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt.

    SECURITY: Uses bcrypt with automatic salt generation.
    Never store plain text passwords.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password

    Example:
        >>> hashed = hash_password("MySecureP@ss123")
        >>> verify_password("MySecureP@ss123", hashed)
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    SECURITY: Constant-time comparison to prevent timing attacks.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("MySecureP@ss123")
        >>> verify_password("MySecureP@ss123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password meets security requirements.

    SECURITY: Enforces password policy defined in config.

    Args:
        password: Password to validate

    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_errors)

    Example:
        >>> valid, errors = validate_password_strength("weak")
        >>> valid
        False
        >>> "Password must be at least 8 characters" in errors
        True
    """
    errors = []

    if len(password) < settings.password_min_length:
        errors.append(f"Password must be at least {settings.password_min_length} characters")

    if settings.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if settings.password_require_digit and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if settings.password_require_special:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.

    SECURITY: Token includes expiration and should be short-lived.
    Use refresh tokens for long-term sessions.

    Args:
        data: Payload data to encode in token (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> # Token valid for default duration (30 min)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token.

    SECURITY: Refresh tokens are long-lived and should be stored securely.
    Used to obtain new access tokens without re-authentication.

    Args:
        data: Payload data to encode in token (e.g., {"sub": user_id})

    Returns:
        str: Encoded JWT refresh token

    Example:
        >>> token = create_refresh_token({"sub": "user123"})
        >>> # Token valid for 7 days by default
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token.

    SECURITY: Validates signature and expiration.
    Returns None if token is invalid or expired.

    Args:
        token: JWT token to decode

    Returns:
        Optional[dict]: Decoded payload if valid, None otherwise

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user123'
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token_type(payload: dict, expected_type: str) -> bool:
    """Verify the token type matches expected type.

    SECURITY: Prevents using refresh tokens as access tokens and vice versa.

    Args:
        payload: Decoded JWT payload
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        bool: True if type matches, False otherwise

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> verify_token_type(payload, "access")
        True
        >>> verify_token_type(payload, "refresh")
        False
    """
    return payload.get("type") == expected_type


def extract_user_id_from_token(token: str, token_type: str = "access") -> Optional[str]:
    """Extract user ID from a JWT token.

    SECURITY: Validates token and type before extracting user ID.

    Args:
        token: JWT token
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Optional[str]: User ID if valid, None otherwise

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> extract_user_id_from_token(token)
        'user123'
    """
    payload = decode_token(token)
    if not payload:
        return None

    if not verify_token_type(payload, token_type):
        return None

    return payload.get("sub")
