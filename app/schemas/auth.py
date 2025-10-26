"""Authentication schemas for request/response validation.

SECURITY: Input validation for auth endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validation import validate_phone_number


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")
    password: str = Field(..., min_length=8, description="Password")

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, max_length=20)

    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="India", max_length=50)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Indian phone number format."""
        if not validate_phone_number(v):
            raise ValueError("Invalid Indian phone number format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "rajesh.kumar@example.com",
                "phone": "+919876543210",
                "password": "SecureP@ss123",
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "date_of_birth": "1990-05-15",
                "gender": "male",
                "address_line1": "123 MG Road",
                "address_line2": "Near City Center",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "country": "India",
            }
        }


class RegisterResponse(BaseModel):
    """User registration response schema."""

    user_id: str
    email: str
    phone: str
    kyc_status: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {"email": "rajesh.kumar@example.com", "password": "SecureP@ss123"}
        }


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class LoginResponse(BaseModel):
    """User login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: dict

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGc...",
                "refresh_token": "eyJhbGc...",
                "token_type": "Bearer",
                "expires_in": 1800,
                "user": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "rajesh.kumar@example.com",
                    "role": "customer",
                    "kyc_status": "verified",
                },
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Logout request schema."""

    refresh_token: str = Field(..., description="Refresh token to revoke")