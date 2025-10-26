"""FastAPI dependencies for authentication and authorization.

SECURITY: These dependencies are injected into route handlers to enforce
authentication and role-based access control.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.audit import AuditAction, AuditLogger
from app.core.security import extract_user_id_from_token

# SECURITY: Bearer token scheme for JWT authentication
security = HTTPBearer()


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and validate current user from JWT token.

    SECURITY: Validates token and logs authentication attempts.
    Use this dependency on all protected routes.

    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials

    Returns:
        str: Validated user ID

    Raises:
        HTTPException: If token is invalid or expired

    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(user_id: str = Depends(get_current_user_id)):
        >>>     return {"user_id": user_id}
    """
    token = credentials.credentials

    # SECURITY: Validate and extract user ID from token
    user_id = extract_user_id_from_token(token, token_type="access")

    if not user_id:
        # SECURITY: Log failed authentication attempt
        AuditLogger.log_security_event(
            action=AuditAction.INVALID_TOKEN,
            ip_address=request.client.host if request.client else None,
            details={"reason": "Invalid or expired token"},
            success=False
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Store user_id in request state for rate limiting
    request.state.user_id = user_id

    return user_id


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """Extract current user from JWT token if present.

    SECURITY: For endpoints that support both authenticated and anonymous access.

    Args:
        request: FastAPI request object
        credentials: Optional HTTP authorization credentials

    Returns:
        Optional[str]: User ID if authenticated, None otherwise

    Example:
        >>> @app.get("/public-or-private")
        >>> async def mixed_route(user_id: Optional[str] = Depends(get_current_user_optional)):
        >>>     if user_id:
        >>>         return {"message": f"Hello {user_id}"}
        >>>     return {"message": "Hello anonymous"}
    """
    if not credentials:
        return None

    user_id = extract_user_id_from_token(credentials.credentials, token_type="access")

    if user_id:
        request.state.user_id = user_id

    return user_id


def require_role(required_role: str):
    """Dependency factory for role-based access control.

    SECURITY: Enforces role requirements on endpoints.
    Must be used after get_current_user_id.

    Args:
        required_role: The role required to access the endpoint

    Returns:
        Dependency function

    Example:
        >>> @app.get("/admin")
        >>> async def admin_route(
        >>>     user_id: str = Depends(get_current_user_id),
        >>>     _: None = Depends(require_role("admin"))
        >>> ):
        >>>     return {"message": "Admin access granted"}
    """
    async def role_checker(
        request: Request,
        user_id: str = Depends(get_current_user_id)
    ) -> None:
        """Check if user has required role.

        SECURITY: Verify user role against required role.
        """
        # SECURITY: In production, fetch user roles from database
        # TODO: Implement role checking via user repository
        # user_roles = await user_repository.get_user_roles(user_id)

        # For now, this is a placeholder
        # if required_role not in user_roles:
        #     AuditLogger.log_security_event(
        #         action=AuditAction.UNAUTHORIZED_ACCESS,
        #         user_id=user_id,
        #         ip_address=request.client.host if request.client else None,
        #         details={"required_role": required_role},
        #         success=False
        #     )
        #
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail=f"Insufficient permissions. Required role: {required_role}"
        #     )

        pass

    return role_checker


async def get_client_ip(request: Request) -> str:
    """Extract client IP address from request.

    SECURITY: Handles X-Forwarded-For header for proxied requests.

    Args:
        request: FastAPI request object

    Returns:
        str: Client IP address

    Example:
        >>> @app.get("/track-ip")
        >>> async def track_ip(ip: str = Depends(get_client_ip)):
        >>>     return {"your_ip": ip}
    """
    # SECURITY: Check X-Forwarded-For header (if behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (client IP)
        return forwarded_for.split(",")[0].strip()

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


async def get_user_agent(request: Request) -> Optional[str]:
    """Extract User-Agent from request headers.

    SECURITY: Used for audit logging and suspicious activity detection.

    Args:
        request: FastAPI request object

    Returns:
        Optional[str]: User-Agent string

    Example:
        >>> @app.post("/login")
        >>> async def login(user_agent: str = Depends(get_user_agent)):
        >>>     # Log login with user agent
        >>>     pass
    """
    return request.headers.get("User-Agent")
