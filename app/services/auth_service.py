"""Authentication service with business logic.

SECURITY: Handles user registration, login, and token management.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditLogger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models import RefreshToken, User
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    """Authentication service for user management."""

    @staticmethod
    def register_user(db: Session, request: RegisterRequest, ip_address: str) -> User:
        """Register a new user.

        SECURITY: Validates password strength, hashes password, creates audit log.

        Args:
            db: Database session
            request: Registration request data
            ip_address: Client IP address

        Returns:
            User: Created user object

        Raises:
            ValueError: If password is weak or email/phone already exists
        """
        # Validate password strength
        is_valid, errors = validate_password_strength(request.password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")

        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise ValueError("Email already registered")

        # Check if phone already exists
        existing_phone = db.query(User).filter(User.phone == request.phone).first()
        if existing_phone:
            raise ValueError("Phone number already registered")

        # Create user
        user = User(
            email=request.email,
            phone=request.phone,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=datetime.strptime(request.date_of_birth, "%Y-%m-%d"),
            gender=request.gender,
            address_line1=request.address_line1,
            address_line2=request.address_line2,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            kyc_status="pending",
            is_verified=False,
            role="customer",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_CREATED,
            user_id=str(user.id),
            ip_address=ip_address,
            resource_type="user",
            resource_id=user.id,
            details={"email": user.email, "phone": user.phone},
        )

        return user

    @staticmethod
    def login_user(
        db: Session, request: LoginRequest, ip_address: str, user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """Authenticate user and generate tokens.

        SECURITY: Verifies password, creates tokens, updates last_login.

        Args:
            db: Database session
            request: Login request data
            ip_address: Client IP address
            user_agent: User agent string

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            ValueError: If credentials are invalid or account is inactive
        """
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()

        if not user:
            # SECURITY: Audit failed login
            AuditLogger.log_security_event(
                action=AuditAction.LOGIN_FAILED,
                ip_address=ip_address,
                details={"email": request.email, "reason": "User not found"},
                success=False,
            )
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            # SECURITY: Audit failed login
            AuditLogger.log_security_event(
                action=AuditAction.LOGIN_FAILED,
                user_id=str(user.id),
                ip_address=ip_address,
                details={"email": request.email, "reason": "Invalid password"},
                success=False,
            )
            raise ValueError("Invalid email or password")

        # Check if account is active
        if not user.is_active:
            AuditLogger.log_security_event(
                action=AuditAction.LOGIN_FAILED,
                user_id=str(user.id),
                ip_address=ip_address,
                details={"reason": "Account inactive"},
                success=False,
            )
            raise ValueError("Account is inactive")

        # Generate tokens
        access_token = create_access_token({"sub": str(user.id), "role": user.role})
        refresh_token_str = create_refresh_token({"sub": str(user.id)})

        # Store refresh token
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_password(refresh_token_str),  # Hash the token
            expires_at=datetime.utcnow() + timedelta(days=7),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(refresh_token)

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # SECURITY: Audit successful login
        AuditLogger.log(
            action=AuditAction.LOGIN_SUCCESS,
            user_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": user.email},
        )

        return user, access_token, refresh_token_str

    @staticmethod
    def logout_user(db: Session, refresh_token_str: str, user_id: str, ip_address: str) -> None:
        """Revoke refresh token on logout.

        SECURITY: Marks token as revoked in database.

        Args:
            db: Database session
            refresh_token_str: Refresh token to revoke
            user_id: User ID
            ip_address: Client IP address
        """
        # Find and revoke token
        token_hash = hash_password(refresh_token_str)
        refresh_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash, RefreshToken.is_revoked == False
            )
            .first()
        )

        if refresh_token:
            refresh_token.is_revoked = True
            refresh_token.revoked_at = datetime.utcnow()
            db.commit()

        # SECURITY: Audit logout
        AuditLogger.log(
            action=AuditAction.LOGOUT, user_id=user_id, ip_address=ip_address
        )