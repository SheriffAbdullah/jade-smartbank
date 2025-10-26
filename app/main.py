"""Main FastAPI application entry point.

SECURITY: Production-ready with CORS, rate limiting, and security headers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.rate_limiting import limiter
from app.db.base import init_db

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Jade SmartBank API",
    description="Secure Banking Platform for India - REST API",
    version="1.0.0",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    contact={
        "name": "Jade SmartBank",
        "email": "api@jadebank.com",
    },
    license_info={
        "name": "MIT",
    },
)

# SECURITY: Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SECURITY: Trusted host middleware (prevent host header attacks)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.jadebank.com", "localhost", "127.0.0.1"]
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup.

    SECURITY: Only creates tables in development. Use Alembic in production.
    """
    # Disabled - using Alembic migrations instead
    # if settings.debug:
    #     init_db()
    pass


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "online",
        "service": "Jade SmartBank API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.debug else "disabled in production"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy"}


# Import and include routers
from app.api.v1.routes import accounts, admin, auth, loans, transactions

app.include_router(auth.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )