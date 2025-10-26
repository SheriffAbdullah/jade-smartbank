"""Authentication routes - Use Case 1.

SECURITY: Registration, login, KYC with rate limiting and audit.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, get_current_user_id
from app.core.rate_limiting import auth_rate_limit_key, limiter
from app.db.base import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.schemas.kyc import KYCDocumentResponse, KYCDocumentUpload, KYCStatusResponse
from app.services.auth_service import AuthService
from app.services.kyc_service import KYCService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new customer account with KYC pending status",
)
@limiter.limit("5/hour", key_func=auth_rate_limit_key)
async def register(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """Register a new user.

    SECURITY:
    - Password strength validation
    - Email and phone uniqueness check
    - Rate limit: 5 registrations per hour per IP
    - Audit logging enabled

    Returns:
        RegisterResponse: User details with pending KYC status
    """
    try:
        user = AuthService.register_user(db, data, ip_address)
        return RegisterResponse(
            user_id=str(user.id),
            email=user.email,
            phone=user.phone,
            kyc_status=user.kyc_status,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user and receive JWT tokens",
)
@limiter.limit("5/minute", key_func=auth_rate_limit_key)
async def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """Login user and generate tokens.

    SECURITY:
    - Bcrypt password verification
    - JWT token generation (access + refresh)
    - Rate limit: 5 login attempts per minute
    - Audit logging for success/failure

    Returns:
        LoginResponse: Access token, refresh token, and user info
    """
    try:
        user_agent = request.headers.get("user-agent")
        user, access_token, refresh_token = AuthService.login_user(
            db, data, ip_address, user_agent
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=1800,  # 30 minutes
            user={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role,
                "kyc_status": user.kyc_status,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {str(e)}"
        )


@router.get(
    "/me",
    summary="Get current user",
    description="Get currently authenticated user details",
)
async def get_me(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current user details.

    SECURITY: Requires valid JWT access token.

    Returns:
        Current user information
    """
    from app.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "user_id": str(user.id),
        "email": user.email,
        "phone": user.phone,
        "full_name": user.full_name,
        "kyc_status": user.kyc_status,
        "role": user.role,
        "is_active": user.is_active,
    }


# KYC Routes
@router.post(
    "/kyc/documents",
    response_model=KYCDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload KYC document",
    description="Upload KYC document for verification",
)
async def upload_kyc_document(
    request: Request,
    document_type: str = Form(...),
    document_number: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    ip_address: str = Depends(get_client_ip),
):
    """Upload KYC document.

    SECURITY:
    - Requires authentication
    - Validates document format and file type
    - Stores document file

    Returns:
        KYCDocumentResponse: Uploaded document details
    """
    try:
        document = await KYCService.upload_document(db, user_id, document_type, document_number, file, ip_address)
        return KYCDocumentResponse(
            document_id=str(document.id),
            document_type=document.document_type,
            document_number=document.document_number,
            is_verified=document.is_verified,
            verified_at=document.verified_at,
            created_at=document.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/kyc/status",
    response_model=KYCStatusResponse,
    summary="Get KYC status",
    description="Get user's KYC verification status and documents",
)
async def get_kyc_status(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get KYC status and documents.

    SECURITY: Requires authentication

    Returns:
        KYCStatusResponse: KYC status and document list
    """
    from app.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    documents = KYCService.get_user_documents(db, user_id)

    return KYCStatusResponse(
        kyc_status=user.kyc_status,
        documents=[
            KYCDocumentResponse(
                document_id=str(doc.id),
                document_type=doc.document_type,
                document_number=doc.document_number,
                is_verified=doc.is_verified,
                verified_at=doc.verified_at,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
    )