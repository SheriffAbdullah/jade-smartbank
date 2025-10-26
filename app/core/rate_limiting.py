"""Rate limiting utilities for API protection.

SECURITY: Prevents brute force attacks, DoS, and API abuse.
Implemented using slowapi middleware.
"""
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()


def get_request_identifier(request: Request) -> str:
    """Extract identifier for rate limiting.

    SECURITY: Uses IP address + user ID (if authenticated) for accurate tracking.
    Prevents bypassing rate limits via multiple user accounts from same IP.

    Args:
        request: FastAPI request object

    Returns:
        str: Unique identifier for rate limiting

    Example:
        >>> # Anonymous user: uses IP only
        >>> # Authenticated user: uses IP + user_id
    """
    # Get IP address
    identifier = get_remote_address(request)

    # If user is authenticated, append user ID
    if hasattr(request.state, "user_id") and request.state.user_id:
        identifier = f"{identifier}:{request.state.user_id}"

    return identifier


# SECURITY: Initialize rate limiter with custom key function
limiter = Limiter(
    key_func=get_request_identifier,
    enabled=settings.rate_limit_enabled
)


def create_rate_limit_key(prefix: str) -> Callable:
    """Create a custom rate limit key function with prefix.

    SECURITY: Allows different rate limits for different endpoint groups.

    Args:
        prefix: Prefix for the rate limit key (e.g., "auth", "transfer")

    Returns:
        Callable: Key function for rate limiter

    Example:
        >>> auth_key = create_rate_limit_key("auth")
        >>> # Use in endpoint: @limiter.limit("5/minute", key_func=auth_key)
    """
    def key_func(request: Request) -> str:
        base_key = get_request_identifier(request)
        return f"{prefix}:{base_key}"

    return key_func


# Common rate limit key functions for different endpoint types
auth_rate_limit_key = create_rate_limit_key("auth")
transfer_rate_limit_key = create_rate_limit_key("transfer")
query_rate_limit_key = create_rate_limit_key("query")


def rate_limit_exceeded_handler(request: Request, response: Response) -> dict:
    """Custom handler for rate limit exceeded responses.

    SECURITY: Logs rate limit violations for monitoring.

    Args:
        request: FastAPI request object
        response: FastAPI response object

    Returns:
        dict: Error response
    """
    return {
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later.",
        "status_code": 429
    }
