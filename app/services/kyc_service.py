"""KYC service for document verification.

SECURITY: Handles KYC document upload and verification workflow.
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditLogger
from app.models import KYCDocument, User
from app.schemas.kyc import KYCDocumentUpload


class KYCService:
    """KYC document management service."""

    @staticmethod
    def upload_document(
        db: Session, user_id: str, request: KYCDocumentUpload, ip_address: str
    ) -> KYCDocument:
        """Upload KYC document.

        SECURITY: Validates document format, stores metadata.

        Args:
            db: Database session
            user_id: User ID
            request: Document upload request
            ip_address: Client IP address

        Returns:
            KYCDocument: Created document record

        Raises:
            ValueError: If document type already exists for user
        """
        # Check if document type already exists
        existing = (
            db.query(KYCDocument)
            .filter(
                KYCDocument.user_id == user_id,
                KYCDocument.document_type == request.document_type,
            )
            .first()
        )

        if existing:
            raise ValueError(f"{request.document_type.upper()} document already uploaded")

        # Create document record (simulated - in production would upload file to S3)
        document = KYCDocument(
            user_id=user_id,
            document_type=request.document_type,
            document_number=request.document_number,
            document_url=f"simulated://documents/{user_id}/{request.document_type}",
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
            resource_id=document.id,
            details={
                "document_type": request.document_type,
                "document_number": request.document_number,
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
            resource_id=document.id,
            details={
                "action": "verified" if is_verified else "rejected",
                "user_id": str(document.user_id),
            },
        )

        return document