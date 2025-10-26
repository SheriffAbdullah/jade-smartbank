"""KYC service for document verification.

SECURITY: Handles KYC document upload and verification workflow.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditLogger
from app.core.validation import validate_pan_number
from app.models import KYCDocument, User
from app.schemas.kyc import KYCDocumentUpload


class KYCService:
    """KYC document management service."""

    @staticmethod
    async def upload_document(
        db: Session,
        user_id: str,
        document_type: str,
        document_number: str,
        file: UploadFile,
        ip_address: str
    ) -> KYCDocument:
        """Upload KYC document.

        SECURITY: Validates document format, stores file, creates metadata.

        Args:
            db: Database session
            user_id: User ID
            document_type: Type of document (pan, aadhaar, etc.)
            document_number: Document number
            file: Uploaded file
            ip_address: Client IP address

        Returns:
            KYCDocument: Created document record

        Raises:
            ValueError: If validation fails or document type already exists
        """
        # Validate document type
        valid_types = ["pan", "aadhaar", "passport", "driving_license"]
        if document_type.lower() not in valid_types:
            raise ValueError(f"Document type must be one of: {', '.join(valid_types)}")

        document_type = document_type.lower()

        # Validate document number
        if document_type == "pan":
            if not validate_pan_number(document_number):
                raise ValueError("Invalid PAN number format")

        # Validate file type
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        content = await file.read()
        if len(content) > max_size:
            raise ValueError("File size exceeds 5MB limit")
        await file.seek(0)  # Reset file pointer

        # Check if document type already exists
        existing = (
            db.query(KYCDocument)
            .filter(
                KYCDocument.user_id == user_id,
                KYCDocument.document_type == document_type,
            )
            .first()
        )

        if existing:
            raise ValueError(f"{document_type.upper()} document already uploaded")

        # Save file to uploads directory
        upload_dir = Path("/app/uploads/kyc")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{user_id}_{document_type}_{file_id}{file_ext}"
        file_path = upload_dir / filename

        # Write file
        with open(file_path, "wb") as f:
            f.write(content)

        # Create document record
        document = KYCDocument(
            user_id=user_id,
            document_type=document_type,
            document_number=document_number.upper(),
            document_url=f"/uploads/kyc/{filename}",
            is_verified=False,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_UPDATED,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="kyc_document",
            resource_id=str(document.id),
            details={
                "document_type": document_type,
                "document_number": document_number,
                "filename": filename,
            },
        )

        return document

    @staticmethod
    def get_user_documents(db: Session, user_id: str) -> List[KYCDocument]:
        """Get all KYC documents for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of KYC documents
        """
        return db.query(KYCDocument).filter(KYCDocument.user_id == user_id).all()

    @staticmethod
    def verify_document(
        db: Session,
        document_id: str,
        admin_id: str,
        is_verified: bool,
        rejection_reason: str = None,
        ip_address: str = None,
    ) -> KYCDocument:
        """Verify or reject KYC document (Admin only).

        SECURITY: Updates user KYC status based on verified documents.

        Args:
            db: Database session
            document_id: Document ID
            admin_id: Admin user ID
            is_verified: Verification status
            rejection_reason: Reason for rejection
            ip_address: Client IP address

        Returns:
            KYCDocument: Updated document

        Raises:
            ValueError: If document not found
        """
        document = db.query(KYCDocument).filter(KYCDocument.id == document_id).first()

        if not document:
            raise ValueError("Document not found")

        # Update document
        document.is_verified = is_verified
        document.verified_by = admin_id
        document.verified_at = datetime.utcnow()
        document.rejection_reason = rejection_reason if not is_verified else None

        # Update user KYC status
        if is_verified:
            # Check if user has at least 2 verified documents (PAN + one more)
            user = db.query(User).filter(User.id == document.user_id).first()
            verified_docs = (
                db.query(KYCDocument)
                .filter(
                    KYCDocument.user_id == document.user_id,
                    KYCDocument.is_verified == True,
                )
                .count()
            )

            if verified_docs >= 2:
                user.kyc_status = "verified"
                user.is_verified = True

        db.commit()
        db.refresh(document)

        # SECURITY: Audit log
        AuditLogger.log(
            action=AuditAction.ACCOUNT_UPDATED,
            user_id=admin_id,
            ip_address=ip_address,
            resource_type="kyc_document",
            resource_id=str(document.id),
            details={
                "action": "verified" if is_verified else "rejected",
                "user_id": str(document.user_id),
            },
        )

        return document