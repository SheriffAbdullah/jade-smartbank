"""Seed dummy data for demo purposes.

Creates test users with accounts, transactions, and loans.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.base import SessionLocal
from app.models import User, Account, Transaction, Loan, LoanEMIPayment, KYCDocument
from app.core.security import get_password_hash
from app.utils.account_generator import generate_account_number
import uuid


def seed_data():
    """Seed dummy data for demonstration."""
    db = SessionLocal()

    try:
        print("🌱 Seeding dummy data...")

        # Check if demo user already exists
        existing = db.query(User).filter(User.email == "demo@jadebank.com").first()
        if existing:
            print("✓ Demo data already exists!")
            return

        # 1. Create Demo Customer
        print("\n1️⃣  Creating demo customer...")
        demo_customer = User(
            id=uuid.uuid4(),
            email="demo@jadebank.com",
            phone="+6591234567",
            password_hash=get_password_hash("Demo@123"),  # Password: Demo@123
            first_name="Demo",
            last_name="Customer",
            date_of_birth=datetime(1990, 1, 1).date(),
            gender="male",
            address_line1="123 Demo Street",
            address_line2="Unit 45",
            city="Singapore",
            state="Singapore",
            postal_code="123456",
            country="Singapore",
            kyc_status="verified",
            role="customer",
            is_active=True,
            is_verified=True,
        )
        db.add(demo_customer)
        db.flush()
        print(f"   ✓ Email: demo@jadebank.com")
        print(f"   ✓ Password: Demo@123")

        # 2. Create KYC Document
        print("\n2️⃣  Creating KYC document...")
        kyc_doc = KYCDocument(
            id=uuid.uuid4(),
            user_id=demo_customer.id,
            document_type="pan",
            document_number="ABCDE1234F",
            file_path="/uploads/demo_pan.pdf",
            is_verified=True,
            verified_at=datetime.utcnow(),
        )
        db.add(kyc_doc)

        # 3. Create Savings Account with Balance
        print("\n3️⃣  Creating savings account...")
        savings_account = Account(
            id=uuid.uuid4(),
            user_id=demo_customer.id,
            account_number=generate_account_number(),
            account_type="savings",
            currency="SGD",
            balance=Decimal("50000.00"),  # ₹50,000
            status="active",
        )
        db.add(savings_account)
        db.flush()
        print(f"   ✓ Account: {savings_account.account_number}")
        print(f"   ✓ Balance: SGD 50,000")

        # 4. Create Current Account
        print("\n4️⃣  Creating current account...")
        current_account = Account(
            id=uuid.uuid4(),
            user_id=demo_customer.id,
            account_number=generate_account_number(),
            account_type="current",
            currency="SGD",
            balance=Decimal("25000.00"),  # ₹25,000
            status="active",
        )
        db.add(current_account)
        db.flush()
        print(f"   ✓ Account: {current_account.account_number}")
        print(f"   ✓ Balance: SGD 25,000")

        # 5. Create Sample Transactions
        print("\n5️⃣  Creating sample transactions...")
        transactions = [
            Transaction(
                id=uuid.uuid4(),
                account_id=savings_account.id,
                transaction_type="deposit",
                amount=Decimal("50000.00"),
                balance_after=Decimal("50000.00"),
                description="Initial deposit",
                reference_number=f"TXN{uuid.uuid4().hex[:10].upper()}",
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=30),
            ),
            Transaction(
                id=uuid.uuid4(),
                account_id=current_account.id,
                transaction_type="deposit",
                amount=Decimal("25000.00"),
                balance_after=Decimal("25000.00"),
                description="Initial deposit",
                reference_number=f"TXN{uuid.uuid4().hex[:10].upper()}",
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=30),
            ),
            Transaction(
                id=uuid.uuid4(),
                from_account_id=savings_account.id,
                to_account_id=current_account.id,
                transaction_type="transfer",
                amount=Decimal("10000.00"),
                balance_after=Decimal("40000.00"),
                description="Transfer to current account",
                reference_number=f"TXN{uuid.uuid4().hex[:10].upper()}",
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=15),
            ),
        ]

        for txn in transactions:
            db.add(txn)
        print(f"   ✓ Created {len(transactions)} transactions")

        # 6. Create Active Loan
        print("\n6️⃣  Creating personal loan...")
        loan = Loan(
            id=uuid.uuid4(),
            user_id=demo_customer.id,
            loan_type="personal",
            principal_amount=Decimal("100000.00"),
            interest_rate=Decimal("12.5"),
            tenure_months=24,
            emi_amount=Decimal("4707.35"),
            outstanding_amount=Decimal("85000.00"),
            disbursement_account_id=savings_account.id,
            purpose="Home renovation",
            status="active",
            disbursed_at=datetime.utcnow() - timedelta(days=120),
            emis_paid=4,
        )
        db.add(loan)
        db.flush()
        print(f"   ✓ Loan Amount: SGD 100,000")
        print(f"   ✓ EMI: SGD 4,707.35/month")
        print(f"   ✓ EMIs Paid: 4/24")

        # 7. Create EMI Payments
        print("\n7️⃣  Creating EMI payment history...")
        for i in range(4):
            emi_payment = LoanEMIPayment(
                id=uuid.uuid4(),
                loan_id=loan.id,
                emi_number=i + 1,
                emi_amount=Decimal("4707.35"),
                principal_component=Decimal("3666.02"),
                interest_component=Decimal("1041.33"),
                outstanding_after=Decimal("100000.00") - (Decimal("3666.02") * (i + 1)),
                payment_date=datetime.utcnow() - timedelta(days=90 - (i * 30)),
                status="paid",
            )
            db.add(emi_payment)
        print(f"   ✓ Created 4 EMI payment records")

        # 8. Create Admin User
        print("\n8️⃣  Creating admin user...")
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@jadebank.com",
            phone="+6598765432",
            password_hash=get_password_hash("Admin@123"),  # Password: Admin@123
            first_name="Admin",
            last_name="User",
            date_of_birth=datetime(1985, 1, 1).date(),
            gender="female",
            address_line1="456 Admin Avenue",
            city="Singapore",
            state="Singapore",
            postal_code="654321",
            country="Singapore",
            kyc_status="verified",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)
        print(f"   ✓ Email: admin@jadebank.com")
        print(f"   ✓ Password: Admin@123")

        db.commit()

        print("\n" + "=" * 60)
        print("✅ DUMMY DATA SEEDED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 DEMO CREDENTIALS:")
        print("\n👤 Customer Account:")
        print("   Email:    demo@jadebank.com")
        print("   Password: Demo@123")
        print(f"   Savings:  {savings_account.account_number} (SGD 50,000)")
        print(f"   Current:  {current_account.account_number} (SGD 25,000)")
        print("   Loan:     SGD 100,000 Personal Loan (4/24 EMIs paid)")
        print("\n👨‍💼 Admin Account:")
        print("   Email:    admin@jadebank.com")
        print("   Password: Admin@123")
        print("\n🌐 Login at: https://jade-smartbank-frontend.vercel.app")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()