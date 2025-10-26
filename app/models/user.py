"""User model for authentication and profile management.

SECURITY: Password hashes only, no plain text passwords.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User model for customer and admin accounts.

    SECURITY: Stores bcrypt password hashes, tracks KYC status and roles.
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(254), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Personal Details
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(20))

    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(10), nullable=False)
    country = Column(String(50), default="India")

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    kyc_status = Column(
        String(20), default="pending", index=True
    )  # pending, verified, rejected

    # Role
    role = Column(String(20), default="customer")  # customer, admin, auditor

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    kyc_documents = relationship("KYCDocument", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"