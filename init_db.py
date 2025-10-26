"""Initialize database schema.

Run this script to create all database tables.
Usage: python init_db.py
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.base import Base, engine
from app.models import (
    Account,
    AuditLog,
    DailyTransferTracking,
    KYCDocument,
    Loan,
    LoanEMIPayment,
    RefreshToken,
    Transaction,
    User,
)


def init_database():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()