"""Database base configuration and session management.

SECURITY: Connection pooling and proper session handling.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# SECURITY: Connection pooling for production
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database session dependency for FastAPI.

    Yields:
        Session: Database session that auto-closes after request

    Example:
        >>> @app.get("/users")
        >>> def get_users(db: Session = Depends(get_db)):
        >>>     return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables.

    SECURITY: Only use in development. Use Alembic migrations in production.
    """
    Base.metadata.create_all(bind=engine)