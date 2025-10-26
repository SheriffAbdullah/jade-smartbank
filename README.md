# Jade - A Modular Smart Bank Backend

## Tech Stack

**Backend:** FastAPI
**Database:** PostgreSQL
**ORM:** SQLModel
**Auth:** JWT + Bcrypt
**Security:** slowapi for Rate Limiting, input validation
**Testing:** pytest, httpx
**Deployment:** Docker + Render
**Audit:** Standard audit log
**Virtual Environment:** venv

## Approach

1. 1 hour
- Define data models
2. 2 hours
- Implement auth with JWT + roles
3. 1 hour
- Add rate limiting, password hashing, RBAC
- Implement audit logger
4. 1 hour
- Write key test cases
- Document APIs via Swagger
- Dockerize + host

## Structure

**app/core/**
config.py
- Pull configurations from `.env` file
- Password Policy, Rate Limiting, Database, CORS, Logging

security.py
- Password Hashing
- Hash Verification
- Password Strength Verification
- JWT Access Token (Create, Refresh, Decode, Verify)

validation.py
- Input sanitaton
- Email, phone, amount, account number, KYC validation

dependencies.py
- Configure FastAPI
- JWT parsing
- Security Roles Enforcing (Admin/User)
- User IP checking

audit.py
- Authentication (logins, updates, etc.)
- Account Management (account crud + locking)
- Transactions (initiation, completion, failures, etc)
- Loans
- Security Events
- Setting Audit Levels
- Log Format

rate_limiting.py
- Rate limits
- Exceeded Handler

**app/tests/**
test_security.py
- Hashing
- Password (success, failure, etc.)
- JWT Tokens

test_validation.py
- Input validation
- Email, Phone, Amount, KYC Numbers, etc.

conftest.py
- Setup demo users

**requirements.txt**
- Dependencies


