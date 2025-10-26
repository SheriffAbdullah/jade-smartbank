"""Audit logging for security and compliance.

SECURITY: All sensitive operations must be audited with timestamp, user ID, and IP.
Audit logs are append-only and should never be deleted.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AuditAction(str, Enum):
    """Enumeration of auditable actions.

    SECURITY: Comprehensive list of actions that must be logged.
    """
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    TOKEN_REFRESHED = "token_refreshed"

    # Account Management
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_UPDATED = "account_updated"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"

    # Transactions
    TRANSFER_INITIATED = "transfer_initiated"
    TRANSFER_COMPLETED = "transfer_completed"
    TRANSFER_FAILED = "transfer_failed"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

    # Loans
    LOAN_APPLICATION = "loan_application"
    LOAN_APPROVED = "loan_approved"
    LOAN_REJECTED = "loan_rejected"
    LOAN_PAYMENT = "loan_payment"

    # Security Events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditLevel(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(BaseModel):
    """Audit log entry model.

    SECURITY: Immutable record of all security-relevant events.
    """
    timestamp: datetime
    action: AuditAction
    level: AuditLevel
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    success: bool = True


class AuditLogger:
    """Centralized audit logging service.

    SECURITY: All audit logs must be stored in a tamper-proof manner.
    Consider using write-once storage or blockchain for critical systems.
    """

    @staticmethod
    def log(
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = True
    ) -> AuditLog:
        """Create and store an audit log entry.

        SECURITY: This method should write to a dedicated audit table
        with append-only permissions.

        Args:
            action: The action being audited
            level: Severity level
            user_id: ID of user performing action
            ip_address: IP address of request
            user_agent: User agent string
            resource_type: Type of resource (e.g., "account", "transaction")
            resource_id: ID of affected resource
            details: Additional context as dict
            success: Whether the action succeeded

        Returns:
            AuditLog: The created audit log entry

        Example:
            >>> AuditLogger.log(
            ...     action=AuditAction.LOGIN_SUCCESS,
            ...     user_id="user123",
            ...     ip_address="192.168.1.1"
            ... )
        """
        audit_entry = AuditLog(
            timestamp=datetime.utcnow(),
            action=action,
            level=level,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            success=success
        )

        # SECURITY: In production, persist to database
        # TODO: Implement database storage in services layer
        # await audit_repository.create(audit_entry)

        return audit_entry

    @staticmethod
    def log_security_event(
        action: AuditAction,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = False
    ) -> AuditLog:
        """Log a security-related event.

        SECURITY: All security events are logged at WARNING or higher level.

        Args:
            action: The security action being audited
            user_id: ID of user (if known)
            ip_address: IP address of request
            details: Additional context
            success: Whether the action succeeded

        Returns:
            AuditLog: The created audit log entry

        Example:
            >>> AuditLogger.log_security_event(
            ...     action=AuditAction.UNAUTHORIZED_ACCESS,
            ...     ip_address="192.168.1.1",
            ...     details={"endpoint": "/admin/users"}
            ... )
        """
        return AuditLogger.log(
            action=action,
            level=AuditLevel.WARNING if success else AuditLevel.ERROR,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=success
        )
