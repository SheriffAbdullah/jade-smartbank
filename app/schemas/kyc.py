"""KYC schemas for document verification."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.validation import validate_pan_number


class KYCDocumentUpload(BaseModel):
    """KYC document upload request schema."""

    document_type: str = Field(
        ..., description="Document type: pan, aadhaar, passport, driving_license"
    )
    document_number: str = Field(..., min_length=5, max_length=50)

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        """Validate document type."""
        valid_types = ["pan", "aadhaar", "passport", "driving_license"]
        if v.lower() not in valid_types:
            raise ValueError(f"Document type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @field_validator("document_number")
    @classmethod
    def validate_document_number(cls, v: str, info) -> str:
        """Validate document number based on type."""
        document_type = info.data.get("document_type", "").lower()

        if document_type == "pan":
            if not validate_pan_number(v):
                raise ValueError("Invalid PAN number format")

        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {"document_type": "pan", "document_number": "ABCDE1234F"}
        }


class KYCDocumentResponse(BaseModel):
    """KYC document response schema."""

    document_id: str
    document_type: str
    document_number: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class KYCStatusResponse(BaseModel):
    """KYC status response schema."""

    kyc_status: str
    documents: list[KYCDocumentResponse]

    class Config:
        from_attributes = True


class KYCVerificationRequest(BaseModel):
    """KYC verification request schema for admin."""

    is_verified: bool = Field(..., description="Verification status")
    admin_notes: Optional[str] = Field(None, max_length=500, description="Admin verification notes")

    class Config:
        json_schema_extra = {
            "example": {
                "is_verified": True,
                "admin_notes": "All documents verified successfully"
            }
        }