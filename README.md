# 🏦 Jade SmartBank

**Secure Banking Platform for India** - A modern, cloud-ready banking API built with FastAPI, PostgreSQL, and industry-standard security practices.

Frontend at: https://github.com/SheriffAbdullah/jade-smartbank-frontend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Features

### ✅ Implemented Use Cases

- **Use Case 1**: User Registration & KYC Verification
- **Use Case 2**: Account Creation (Savings/Current/FD)
- **Use Case 3**: Money Transfer & Transactions
- **Use Case 4**: Loan Application & EMI Management

### 🔐 Security Features

- **Authentication**: JWT-based (Access + Refresh tokens)
- **Password Security**: Bcrypt hashing with strength validation
- **Input Validation**: Indian banking validators (PAN, IFSC, phone, etc.)
- **Rate Limiting**: Protection against brute force and DoS
- **Audit Logging**: Complete security trail for compliance
- **RBAC**: Role-based access control (Customer/Admin/Auditor)

### 🇮🇳 Indian Banking Context

- **Phone Numbers**: 10-digit format starting with 6-9
- **PAN Validation**: ABCDE1234F format
- **IFSC Codes**: SBIN0001234 format
- **Account Numbers**: 9-18 digit validation
- **Currency**: INR (₹) with Decimal precision

### 🏗️ Architecture

- **Framework**: FastAPI (async, high-performance)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic for version control
- **Deployment**: Docker + Docker Compose
- **Cloud**: Render.com ready (one-click deploy)

---

## 📋 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/jade-smartbank.git
cd jade-smartbank

# Copy environment file
cp .env.example .env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env file

# Start services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head

# Access API
open http://localhost:8000
open http://localhost:8000/api/docs  # Swagger UI
```

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/jade-smartbank.git
cd jade-smartbank

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb jade_smartbank

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# Access API
open http://localhost:8000/api/docs
```

---

## 📊 Database Schema

### Core Tables (9)

| Table | Purpose | Records |
|-------|---------|---------|
| `users` | User profiles & authentication | Customers, admins, auditors |
| `kyc_documents` | KYC verification | PAN, Aadhaar, passport |
| `accounts` | Bank accounts | Savings, current, FD |
| `transactions` | Financial transactions | Transfers, deposits, withdrawals |
| `daily_transfer_tracking` | Daily limit enforcement | Per-account tracking |
| `loans` | Loan applications | All loan types |
| `loan_emi_payments` | EMI tracking | Monthly installments |
| `audit_logs` | Security audit trail | All operations |
| `refresh_tokens` | JWT token management | Token storage |

**See**: [DATABASE_DESIGN.md](DOCS/DATABASE_DESIGN.md) for complete schema

---

## 🔗 API Endpoints

### Authentication (7 endpoints)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/kyc/documents` - Upload KYC document
- `GET /api/v1/kyc/status` - Get KYC status
- `PUT /api/v1/admin/kyc/documents/{id}/verify` - Verify KYC (Admin)

### Accounts (4 endpoints)
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/accounts` - List accounts
- `GET /api/v1/accounts/{id}` - Get account details
- `GET /api/v1/accounts/{id}/statement` - Account statement

### Transactions (5 endpoints)
- `POST /api/v1/transactions/transfer` - Transfer money
- `POST /api/v1/transactions/deposit` - Deposit money
- `POST /api/v1/transactions/withdraw` - Withdraw money
- `GET /api/v1/transactions/{id}` - Get transaction
- `GET /api/v1/transactions` - Transaction history

### Loans (7 endpoints)
- `POST /api/v1/loans/calculate-emi` - Calculate EMI
- `POST /api/v1/loans` - Apply for loan
- `GET /api/v1/loans` - List loans
- `GET /api/v1/loans/{id}` - Loan details
- `GET /api/v1/loans/{id}/emi-schedule` - EMI schedule
- `POST /api/v1/loans/{id}/pay-emi` - Pay EMI
- `PUT /api/v1/admin/loans/{id}/review` - Review loan (Admin)

**See**: [API_ENDPOINTS.md](DOCS/API_ENDPOINTS.md) for complete API documentation

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html

# Run specific test file
pytest app/tests/test_security.py

# Run with verbose output
pytest -v
```

**Coverage Target**: ≥85%

**Test Files**:
- `test_security.py` - Password hashing, JWT validation
- `test_validation.py` - Input validators (PAN, IFSC, phone, etc.)

---

## 🚀 Deployment

### Render.com (One-Click Deploy)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

1. Click "Deploy to Render"
2. Connect GitHub repository
3. Render auto-configures from `render.yaml`
4. API goes live at: `https://jade-smartbank-api.onrender.com`

**See**: [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide

### Manual Deployment

```bash
# Build Docker image
docker build -t jade-smartbank .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=$DATABASE_URL \
  -e SECRET_KEY=$SECRET_KEY \
  jade-smartbank
```

---

## 📁 Project Structure

```
jade-smartbank/
├── app/
│   ├── api/v1/routes/          # API endpoints (TODO)
│   ├── core/                   # Config, security, validation
│   │   ├── config.py          # Environment configuration
│   │   ├── security.py        # Password, JWT helpers
│   │   ├── validation.py      # Input validators
│   │   ├── rate_limiting.py   # Rate limit config
│   │   ├── audit.py           # Audit logging
│   │   └── dependencies.py    # FastAPI dependencies
│   ├── db/                    # Database setup
│   │   ├── base.py           # SQLAlchemy base
│   │   └── __init__.py
│   ├── models/               # SQLAlchemy models (9 tables)
│   │   ├── user.py
│   │   ├── kyc_document.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── daily_transfer_tracking.py
│   │   ├── loan.py
│   │   ├── loan_emi_payment.py
│   │   ├── audit_log.py
│   │   └── refresh_token.py
│   ├── schemas/              # Pydantic schemas (TODO)
│   ├── services/             # Business logic (TODO)
│   ├── repositories/         # Data access (TODO)
│   ├── tests/                # Test suite
│   │   ├── test_security.py
│   │   ├── test_validation.py
│   │   └── conftest.py
│   └── main.py               # FastAPI app entry point
├── alembic/                   # Database migrations
│   ├── versions/
│   └── env.py
├── DOCS/                      # Documentation
│   ├── PRD.md
│   ├── DATABASE_DESIGN.md
│   ├── API_ENDPOINTS.md
│   └── QUICK_REFERENCE.md
├── .github/workflows/         # CI/CD pipelines
│   └── deploy.yml
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Local development
├── render.yaml               # Render deployment config
├── alembic.ini               # Alembic configuration
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── DEPLOYMENT.md            # Deployment guide
├── SECURITY.md              # Security documentation
├── SETUP.md                 # Setup instructions
└── README.md                # This file
```

---

## 🔒 Security

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character

### Token Management
- **Access Token**: 30 minutes (API calls)
- **Refresh Token**: 7 days (renew access)
- Token type validation prevents misuse

### Rate Limits
- **Authentication**: 5 requests/minute
- **Transfers**: 10 requests/minute
- **Account Operations**: 30 requests/minute
- **Loan Applications**: 5 requests/hour

### Audit Trail
Every critical operation logged:
- User ID, IP address, user agent
- Action type and timestamp
- Resource affected
- Success/failure status

**See**: [SECURITY.md](SECURITY.md) for complete security documentation

---

## 💰 Business Rules

### Account Creation

| Account Type | Min Deposit | Min Balance | Daily Limit |
|--------------|-------------|-------------|-------------|
| Savings | ₹500 | ₹1,000 | ₹1,00,000 |
| Current | ₹5,000 | ₹5,000 | ₹5,00,000 |
| FD | ₹10,000 | N/A | N/A |

### Money Transfer
1. Sufficient balance check
2. Daily limit enforcement
3. Minimum balance maintenance
4. Fraud detection scoring

### Loan EMI Calculation
```
EMI = (P × r × (1+r)^n) / ((1+r)^n - 1)

Where:
  P = Principal amount
  r = Monthly interest rate
  n = Tenure in months

Example:
  ₹5,00,000 @ 12.5% for 36 months = ₹16,607.97/month
```

---

## 🛠️ Development

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/ --max-line-length=120

# Type checking
mypy app/ --ignore-missing-imports
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View migration history
alembic history
```

### Environment Variables

```bash
# Required
SECRET_KEY=<generate-with-secrets.token_urlsafe>
DATABASE_URL=postgresql://user:pass@localhost:5432/jade_smartbank

# Optional (with defaults)
DEBUG=false
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_ENABLED=true
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📚 Documentation

- **[PRD](DOCS/PRD.md)** - Product Requirements
- **[Database Design](DOCS/DATABASE_DESIGN.md)** - Complete schema
- **[API Endpoints](DOCS/API_ENDPOINTS.md)** - All 27 endpoints
- **[Quick Reference](DOCS/QUICK_REFERENCE.md)** - Cheat sheet
- **[Security](SECURITY.md)** - Security features
- **[Setup](SETUP.md)** - Development setup
- **[Deployment](DEPLOYMENT.md)** - Cloud deployment

---

## 🎯 Roadmap

### ✅ Phase 1: Core Features (Current)
- [x] User Registration & KYC
- [x] Account Creation
- [x] Money Transfer
- [x] Loan Application & EMI
- [x] Security helpers
- [x] Database models
- [x] Docker & deployment config

### 🚧 Phase 2: API Implementation (Next)
- [ ] Pydantic schemas
- [ ] Service layer
- [ ] FastAPI routes
- [ ] Integration tests
- [ ] Swagger documentation

### 📅 Phase 3: Advanced Features
- [ ] Scheduled payments
- [ ] Bill payments
- [ ] Card management
- [ ] Investment accounts
- [ ] Mobile app API

### 🔮 Phase 4: Scale & Optimize
- [ ] Redis caching
- [ ] Background jobs (Celery)
- [ ] Real-time notifications
- [ ] Analytics dashboard
- [ ] Load testing & optimization

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Documentation**: [/DOCS](DOCS/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/jade-smartbank/issues)
- **Email**: support@jadebank.com

---

<div align="center">

**Made with ❤️ for secure banking**

[Documentation](DOCS/) • [API Reference](DOCS/API_ENDPOINTS.md) • [Security](SECURITY.md) • [Deploy](DEPLOYMENT.md)

</div>