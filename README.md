# VeriCred Share — Cryptographic Selective Disclosure Platform

<div align="center">

**Securely share your credentials. Reveal only what matters.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript)](https://typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🎯 Overview

VeriCred Share is a **production-grade** verifiable credential sharing platform that uses **Merkle tree proofs** and **Ed25519 digital signatures** to enable cryptographic selective disclosure. Credential holders can choose exactly which fields to share while verifiers can cryptographically confirm authenticity without seeing undisclosed data.

### Key Features

- 🔐 **Merkle Tree Selective Disclosure** — Each credential claim is a leaf in a SHA-256 Merkle tree. Share individual fields with cryptographic inclusion proofs.
- ✍️ **Ed25519 Digital Signatures** — The Merkle root is signed with EdDSA via PyNaCl. Verifiers confirm authenticity with the public key.
- ☑️ **Checkbox-Based Field Selection** — Intuitive UI for selecting which fields to disclose.
- 📱 **QR Code & Share Links** — Time-limited, auto-expiring share links with QR code generation.
- ✅ **Public Verification Page** — No login required. Per-field trust indicators and detailed verification reports.
- 🔒 **JWT Authentication** — Secure user registration/login with bcrypt password hashing.
- ⚡ **Rate Limiting** — SlowAPI-based rate limiting on verification and auth endpoints.
- 🐳 **Docker Compose** — One-command deployment with PostgreSQL, FastAPI, and Next.js.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 15)                     │
│  TypeScript · Tailwind CSS v4 · Shadcn/UI · QR Code · Dark Mode │
├─────────────────────────────────────────────────────────────────┤
│                         REST API (JSON)                          │
├─────────────────────────────────────────────────────────────────┤
│                       Backend (FastAPI)                           │
│  JWT Auth · Rate Limiting · Swagger Docs · Async SQLAlchemy      │
├─────────────────────────────────────────────────────────────────┤
│                    Cryptographic Engine                           │
│  Merkle Tree (SHA-256) · Ed25519 (PyNaCl) · Per-claim Salts     │
├─────────────────────────────────────────────────────────────────┤
│                     PostgreSQL 16                                │
│  Users · Credentials · Shared Presentations                      │
└─────────────────────────────────────────────────────────────────┘
```

### Cryptographic Flow

```
ISSUANCE:
  claims → salt each → leaf = SHA256(key:salt:value) → build Merkle tree → Ed25519 sign(root)

SELECTIVE DISCLOSURE:
  select fields → generate Merkle proof per field → bundle as Verifiable Presentation → share link

VERIFICATION:
  recompute leaf hash → walk Merkle proof to root → verify Ed25519 signature → trust report
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/prajwal816/selective-disclosure-platform.git
cd selective-disclosure-platform

# Copy environment template
cp .env.example .env

# Start all services
docker compose up --build

# Access:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL and create database 'vericred'
# Update DATABASE_URL in .env if needed

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run dev server
npm run dev
```

---

## 📡 API Documentation

Interactive Swagger UI available at **http://localhost:8000/docs**

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | ❌ |
| POST | `/api/v1/auth/login` | Login, get JWT tokens | ❌ |

### Credentials

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/credentials/issue` | Issue signed credential | ✅ |
| GET | `/api/v1/credentials` | List user's credentials | ✅ |
| GET | `/api/v1/credentials/{id}` | Get credential detail | ✅ |

### Selective Disclosure

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/credentials/share` | Create selective share | ✅ |
| GET | `/api/v1/credentials/shares` | List active shares | ✅ |
| DELETE | `/api/v1/credentials/shares/{token}` | Revoke a share | ✅ |

### Verification (Public)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/verify/{token}` | Get & verify presentation | ❌ |
| POST | `/api/v1/verify` | Verify presentation | ❌ |

### Example: Issue a Credential

```bash
curl -X POST http://localhost:8000/api/v1/credentials/issue \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_type": "AcademicCredential",
    "claims": {
      "name": "Prajwal Kumar",
      "degree": "B.Tech Computer Science",
      "university": "IIT Delhi",
      "graduationYear": 2025,
      "cgpa": 8.5,
      "rollNumber": "CS2021001",
      "issuerName": "Academic Records Office"
    }
  }'
```

### Example: Create Selective Share

```bash
curl -X POST http://localhost:8000/api/v1/credentials/share \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "<credential-uuid>",
    "selected_fields": ["name", "degree", "graduationYear"],
    "expiry_hours": 24
  }'
```

---

## 🔐 Cryptographic Design

### Merkle Tree Construction

1. **Leaf computation**: For each claim `(key, value)` with random salt:
   ```
   leaf = SHA256(key + ":" + salt + ":" + JSON(value))
   ```

2. **Tree building**: Leaves are sorted by key for deterministic ordering. Pairs are hashed bottom-up:
   ```
   parent = SHA256(left_child + right_child)
   ```

3. **Odd nodes**: Duplicated to maintain binary tree structure.

### Ed25519 Signing

The Merkle root is bound to the issuer identity and timestamp:
```
payload = "root:{merkle_root}|issuer:{issuer_did}|issued:{timestamp}"
signature = Ed25519.sign(payload, private_key)
```

### Selective Disclosure

For each selected field, a **Merkle inclusion proof** is generated:
- The proof contains sibling hashes at each tree level
- Each step records the sibling's position (left/right)
- The verifier walks the proof from leaf to root and compares against the signed root

### Verification

1. Recompute `leaf = SHA256(key:salt:value)` from disclosed data
2. Walk the Merkle proof: concatenate with siblings, hash at each level
3. Compare computed root with the stored Merkle root
4. Verify Ed25519 signature on the root using the issuer's public key
5. Generate per-field trust indicators and overall trust score

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest -v

# Run crypto tests only (most important)
pytest -v tests/test_crypto.py

# Run with coverage
pytest --cov=app tests/
```

### Test Coverage

- **`test_crypto.py`** — Merkle tree construction, proof generation/verification, tamper detection, Ed25519 signing, full selective disclosure roundtrip
- **`test_auth.py`** — Registration, login, duplicate email, weak password, invalid email
- **`test_share_verify.py`** — Credential issuance, selective sharing, cryptographic verification, share revocation, full end-to-end flow

---

## 📁 Project Structure

```
selective-disclosure-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # Route handlers (auth, credentials, share, verify)
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings
│   │   │   ├── security.py      # JWT + bcrypt
│   │   │   ├── crypto.py        # ⭐ Merkle tree + Ed25519 engine
│   │   │   └── rate_limiter.py  # SlowAPI
│   │   ├── crud/                # Database access layer
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic layer
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   └── main.py              # FastAPI entrypoint
│   ├── tests/                   # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/          # Login & Register pages
│   │   │   ├── dashboard/       # Protected dashboard pages
│   │   │   │   ├── issue/       # Issue credential form
│   │   │   │   ├── share/[id]/  # ⭐ Selective disclosure UI
│   │   │   │   └── shares/      # Share management
│   │   │   └── verify/[token]/  # ⭐ Public verification page
│   │   ├── components/ui/       # Shadcn/UI components
│   │   └── lib/                 # API client, auth context, types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/vericred` |
| `JWT_SECRET_KEY` | JWT signing secret | `change-me-in-production` |
| `ED25519_PRIVATE_KEY_HEX` | Ed25519 private key seed (hex) | Auto-generated |
| `ISSUER_DID` | Issuer decentralized identifier | `did:vericred:issuer:primary` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` |
| `FRONTEND_URL` | Frontend URL for share links | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Backend API URL (frontend) | `http://localhost:8000` |

---

## 🛡️ Security Considerations

- **Password hashing**: bcrypt with automatic salt
- **JWT tokens**: Short-lived access tokens (30 min) + refresh tokens (7 days)
- **Per-claim salts**: Cryptographically random 32-byte salts prevent brute-force
- **Rate limiting**: 20/min on verification, 10/min on auth endpoints
- **Input validation**: Pydantic schemas with strict type/length validation
- **CORS**: Configurable origin whitelist
- **SQL injection**: Prevented by SQLAlchemy ORM parameterization
- **Credential privacy**: Full credentials never exposed via share links

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
