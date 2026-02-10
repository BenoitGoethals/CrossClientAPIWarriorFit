# WarriorFit API

A secure **FastAPI** backend application for managing running events with comprehensive authentication, role-based access control, and SSL/TLS encryption.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Security Architecture](#security-architecture)
- [Authentication & Authorization](#authentication--authorization)
- [SSL/TLS Certificates](#ssltls-certificates)
- [Installation](#installation)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)

---

## Overview

WarriorFit API is a running event management system that provides secure RESTful endpoints to register participants, track finish times, and manage cross recordings during running events.

**Key Technologies:**
- **Backend**: FastAPI (Python 3.14+)
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy (async)
- **Authentication**: OAuth2 + JWT + API Key
- **Password Hashing**: Argon2id (stronger than bcrypt)
- **HTTP Client**: httpx
- **Package Manager**: uv
- **Containerization**: Docker

---

## Features

### Core Features
- 🏃 **Runner Registration** - Register participants for running events
- ⏱️ **Time Tracking** - Record and manage finish times
- 📊 **Cross Management** - Track cross recordings for events
- 🎯 **Event Management** - Access and manage event data

### Security Features
- 🔐 **Dual Authentication** - OAuth2 (JWT tokens) + API Key
- 🛡️ **Role-Based Access Control (RBAC)** - PTI, ADMIN, APTI roles
- 🔒 **Argon2id Password Hashing** - Military-grade encryption
- 🔄 **Automatic Password Migration** - Bcrypt → Argon2id on login
- 📜 **SSL/TLS Encryption** - Self-signed certificates with validation
- ✅ **Certificate Validation** - Automatic checks on startup

---

## Security Architecture

### 🏗️ Multi-Layer Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Request                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   SSL/TLS Layer (HTTPS)                     │
│  • 4096-bit RSA encryption                                  │
│  • Self-signed certificate with SANs                        │
│  • Automatic validation on startup                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Authentication Layer                           │
│                                                             │
│  ┌──────────────────┐       ┌──────────────────┐          │
│  │   API Key Auth   │       │   OAuth2 Auth    │          │
│  │   (Header)       │       │   (JWT Token)    │          │
│  └────────┬─────────┘       └────────┬─────────┘          │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│             Authorization Layer (RBAC)                      │
│  • Check user role: PTI, ADMIN, or APTI                    │
│  • Check user is active                                     │
│  • API keys bypass role checks                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Endpoint                               │
│  • Business logic                                           │
│  • Database operations                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization

### 🔑 Authentication Methods

The API supports **two authentication methods**:

#### 1. API Key Authentication (Full Access)

**Use case:** Server-to-server communication, admin scripts, full access

**How it works:**
- Static API key in configuration
- Bypasses all role-based access controls
- Full access to all endpoints

**Configuration** (`src/config/config.yml`):
```yaml
api:
  secret_key: warriorfit_cross_the_world  # Your API key
```

**Usage:**
```bash
curl -X GET "https://localhost:8555/crosses" \
  -H "X-API-Key: warriorfit_cross_the_world" \
  --cacert src/certs/cert.pem
```

**Python example:**
```python
import httpx

client = httpx.Client(verify="./src/certs/cert.pem")
response = client.get(
    "https://localhost:8555/crosses",
    headers={"X-API-Key": "warriorfit_cross_the_world"}
)
```

#### 2. OAuth2 Password Flow (Role-Based Access)

**Use case:** User authentication, role-based access control

**How it works:**
1. User sends username + password to `/token`
2. Server validates credentials (Argon2id hash verification)
3. Server returns JWT access token (30 min expiration)
4. Client includes token in `Authorization` header
5. Server validates token and checks user role

**Step 1: Login**
```bash
curl -X POST "https://localhost:8555/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password" \
  --cacert src/certs/cert.pem
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Step 2: Use Token**
```bash
curl -X GET "https://localhost:8555/crosses" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --cacert src/certs/cert.pem
```

**Python example:**
```python
from test_api_client import WarriorFitClient

client = WarriorFitClient(
    base_url="https://localhost:8555",
    cert_path="./src/certs/cert.pem"
)

# Login
client.login("username", "password")

# Use authenticated client
crosses = client.get_crosses()
```

### 🛡️ Authorization (Role-Based Access Control)

#### Allowed Roles

Only users with these roles can access the API:

| Role | Access | Description |
|------|--------|-------------|
| **PTI** | ✅ Full | Physical Training Instructor |
| **ADMIN** | ✅ Full | Administrator |
| **APTI** | ✅ Full | Assistant Physical Training Instructor |
| USER | ❌ Denied | Standard user |
| GUEST | ❌ Denied | Guest user |
| PLANNER | ❌ Denied | Event planner |

#### How Authorization Works

```python
# src/main.py - Authorization flow

1. Request arrives with OAuth2 token
2. Token is validated and decoded
3. User information is fetched from database
4. User role is checked against allowed roles: ["PTI", "ADMIN", "APTI"]
5. User active status is verified
6. If authorized → Allow access
7. If unauthorized → HTTP 403 Forbidden
```

**Error Responses:**

```json
// Wrong role
{
  "detail": "Access denied. Required roles: PTI, ADMIN, APTI"
}

// Inactive user
{
  "detail": "User account is inactive"
}

// No authentication
{
  "detail": "Not authenticated"
}
```

### 🔐 Password Security

#### Argon2id Hashing

**Why Argon2id?**
- Winner of Password Hashing Competition (2015)
- Stronger than bcrypt, scrypt, and PBKDF2
- Memory-hard algorithm (resistant to GPU/ASIC attacks)
- Side-channel attack protection

**Configuration:**
```python
# Default parameters (src/core/oauth2.py)
time_cost: 3 iterations
memory_cost: 65536 KiB (64 MiB)
parallelism: 4 threads
algorithm: Argon2id (hybrid mode)
```

**Comparison:**

| Algorithm | Memory Usage | GPU Resistant | Status |
|-----------|--------------|---------------|--------|
| **Argon2id** | 64 MiB | ✅ Strong | Current |
| bcrypt | ~4 KB | ⚠️ Moderate | Legacy support |
| PBKDF2 | Minimal | ❌ Weak | Not used |

#### Automatic Password Migration

When users with old bcrypt passwords log in, their passwords are automatically upgraded to Argon2id:

```python
# Login flow
1. User sends username + password
2. System checks password hash format
3. If bcrypt → Verify with bcrypt
4. If valid → Rehash with Argon2id
5. Update database with new hash
6. Next login → Use Argon2id (stronger!)
```

---

## SSL/TLS Certificates

### 🔒 Certificate Architecture

The API uses **self-signed SSL certificates** for encrypted HTTPS communication.

**Certificate Specifications:**
- **Algorithm**: RSA 4096-bit
- **Signature**: SHA-256
- **Validity**: 365 days
- **Format**: PEM
- **Location**: `src/certs/`

**Subject Alternative Names (SANs):**
- DNS: `localhost`
- DNS: `*.localhost`
- IP: `127.0.0.1`
- IP: `0.0.0.0`

### 📜 Certificate Generation

#### Create New Certificate

```bash
cd /home/benoit/PycharmProjects/CrossClientAPIWarriorFit

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout src/certs/key.pem \
  -out src/certs/cert.pem \
  -days 365 \
  -subj "/C=BE/ST=Brussels/L=Brussels/O=WarriorFit/OU=IT/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:0.0.0.0"

# Set proper permissions
chmod 600 src/certs/key.pem  # Private key (read-only by owner)
chmod 644 src/certs/cert.pem # Certificate (readable by all)
```

#### Verify Certificate

```bash
# Check certificate details
openssl x509 -in src/certs/cert.pem -noout -text | grep -E "(Subject:|Issuer:|Not Before|Not After|DNS:|IP)"

# Check expiration
openssl x509 -in src/certs/cert.pem -noout -dates

# Verify certificate is valid
openssl x509 -in src/certs/cert.pem -noout -checkend 0 && echo "✅ Valid"

# Check certificate and key match
openssl x509 -noout -modulus -in src/certs/cert.pem | openssl md5
openssl rsa -noout -modulus -in src/certs/key.pem | openssl md5
# Both MD5 hashes should match
```

### ✅ Automatic Certificate Validation

The application **automatically validates certificates** on startup:

**Validation Checks:**
1. ✅ Certificate file exists and is readable
2. ✅ Private key file exists and is readable
3. ✅ Certificate is not expired
4. ✅ Certificate expiry warning (if < 30 days)
5. ✅ Private key is valid (RSA key check)
6. ✅ Certificate and key match (modulus comparison)

**Startup Output:**
```
============================================================
Validating SSL certificates...
Certificate valid for 364 days
Private key validation: OK
Certificate and private key: MATCH
✅ SSL certificates validated successfully
============================================================
```

**Failed Validation:**
```
============================================================
SSL CERTIFICATE VALIDATION FAILED!
❌ Certificate EXPIRED 45 days ago!
❌ Certificate and private key DO NOT MATCH!
============================================================
Server startup aborted due to invalid SSL certificates.
```

### 🔧 Client SSL Configuration

#### Python (httpx)

```python
import httpx

# With certificate verification
client = httpx.Client(verify="./src/certs/cert.pem")
response = client.get("https://localhost:8555/crosses")

# Without verification (not recommended)
client = httpx.Client(verify=False)
```

#### Python (requests)

```python
import requests

# With certificate verification
response = requests.get(
    "https://localhost:8555/crosses",
    verify="./src/certs/cert.pem"
)

# Without verification (not recommended)
response = requests.get(
    "https://localhost:8555/crosses",
    verify=False
)
```

#### curl

```bash
# With certificate verification
curl --cacert src/certs/cert.pem https://localhost:8555/crosses

# Without verification (not recommended)
curl -k https://localhost:8555/crosses
```

#### Browser

When accessing `https://localhost:8555/docs` in a browser:

1. Browser shows security warning (self-signed certificate)
2. Click "Advanced" or "Show Details"
3. Click "Proceed to localhost" or "Accept Risk"
4. Access API documentation

**For permanent trust (optional):**
- Import `src/certs/cert.pem` into browser's certificate store
- Mark as trusted for SSL/TLS

---

## Installation

### Prerequisites

- **Python**: 3.14+ (via uv)
- **Database**: PostgreSQL 12+
- **Tools**: openssl, git
- **Optional**: Docker, Docker Compose

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/CrossClientAPIWarriorFit.git
cd CrossClientAPIWarriorFit

# 2. Generate SSL certificates
mkdir -p src/certs
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout src/certs/key.pem \
  -out src/certs/cert.pem \
  -days 365 \
  -subj "/C=BE/ST=Brussels/L=Brussels/O=WarriorFit/OU=IT/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:0.0.0.0"

chmod 600 src/certs/key.pem
chmod 644 src/certs/cert.pem

# 3. Install dependencies
uv sync

# 4. Configure database (src/config/config.yml)
database:
  driver: postgresql+asyncpg
  host: localhost
  port: 5432
  username: your_user
  password: your_password
  database: warriorfit_test

api:
  secret_key: warriorfit_cross_the_world
  oauth2_secret_key: your_jwt_secret_key_change_me
  algorithm: HS256
  access_token_expire_minutes: 30

# 5. Run application
export PYTHONPATH=.
uv run python src/main.py
```

### Docker Deployment

```bash
# Build image

sudo docker stop api-warriorfit-app
sudo docker rm api-warriorfit-app

docker build -t api-warriorfit-app.

# Run container
sudo docker run -d \
  --name api-warriorfit-app \
  -p 8555:8555 \
  --restart unless-stopped \
  -v /home/benoit/path/to/config:/etc/CrossClientAPI \
  api-warriorfit-app

# View logs
docker logs -f warriorfit-api
```

---

## API Documentation

### Interactive Documentation

Once running, access:
- **Swagger UI**: https://localhost:8555/docs
- **ReDoc**: https://localhost:8555/redoc

### Available Endpoints

#### Authentication
- `POST /token` - OAuth2 login (get JWT token)

#### Crosses
- `GET /crosses` - Get all crosses
- `GET /crosses/{id}` - Get specific cross
- `POST /crosses/{cross_id}` - Save cross recordings

#### Runners
- `GET /crosses/runners/{cross_id}` - Get runners for a cross
- `POST /crosses/{serial_number}/{id_cross}` - Add runner to cross

**All endpoints require authentication** (API Key or OAuth2 token)

**PTI, ADMIN, or APTI role required** for OAuth2 access

---

## Testing

### Test Client

We provide a comprehensive test client (`test_api_client.py`):

```bash
# Automated tests
uv run python test_api_client.py

# Interactive mode
uv run python test_api_client.py --interactive

# Bash script (curl-based)
./test_api.sh
```

### Example Tests

```python
from test_api_client import WarriorFitClient

client = WarriorFitClient(
    base_url="https://localhost:8555",
    cert_path="./src/certs/cert.pem"
)

# Test 1: API Key
client.set_api_key("warriorfit_cross_the_world")
crosses = client.get_crosses()
print(f"Retrieved {len(crosses)} crosses")

# Test 2: OAuth2
client.login("username", "password")
cross = client.get_cross(1)

# Test 3: Save recordings
recordings = [
    {"serial_number": "TEST001", "running_time": 125.5}
]
client.save_recordings(1, recordings)
```

See [README_API_CLIENT.md](README_API_CLIENT.md) for detailed testing documentation.

---

## Project Structure

```
CrossClientAPIWarriorFit/
├── src/
│   ├── main.py                 # FastAPI application + certificate validation
│   ├── certs/                  # SSL certificates
│   │   ├── cert.pem           # Public certificate (644)
│   │   └── key.pem            # Private key (600)
│   ├── config/
│   │   └── config.yml         # Application configuration
│   ├── core/
│   │   ├── config_reader.py   # Configuration loader
│   │   ├── db_connection.py   # Database connection
│   │   └── oauth2.py          # Authentication & Argon2id hashing
│   ├── model/
│   │   ├── db_model.py        # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   └── role.py            # User roles enum
│   └── repo/
│       └── cross_repository.py # Database operations
├── test_api_client.py          # Python test client (httpx)
├── test_api.sh                 # Bash test script (curl)
├── README_API_CLIENT.md        # Test client documentation
├── Dockerfile                  # Container configuration
├── pyproject.toml             # Python dependencies
├── uv.lock                    # Locked dependency versions
└── README.md                  # This file
```

---

## Security Best Practices

### Production Deployment

1. **Change Default Secrets**
   ```yaml
   api:
     secret_key: "CHANGE_THIS_STRONG_RANDOM_KEY"
     oauth2_secret_key: "CHANGE_THIS_JWT_SECRET_KEY"
   ```

2. **Use Trusted Certificates**
   - Get certificate from trusted CA (Let's Encrypt, etc.)
   - Or use proper internal PKI

3. **Environment Variables**
   ```bash
   export API_SECRET_KEY="your-secret-key"
   export OAUTH2_SECRET="your-jwt-secret"
   export DB_PASSWORD="your-db-password"
   ```

4. **Database Security**
   - Use strong database passwords
   - Enable SSL for database connections
   - Restrict database access by IP

5. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   ufw allow 8555/tcp  # API port
   ufw enable
   ```

6. **Regular Updates**
   ```bash
   # Update dependencies
   uv sync --upgrade

   # Regenerate certificates (yearly)
   ./generate_certs.sh
   ```

---

## Troubleshooting

### Certificate Issues

**Problem:** SSL certificate validation failed
```bash
# Check certificate
openssl x509 -in src/certs/cert.pem -noout -dates

# Regenerate if expired
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout src/certs/key.pem \
  -out src/certs/cert.pem \
  -days 365 \
  -subj "/C=BE/ST=Brussels/L=Brussels/O=WarriorFit/OU=IT/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:0.0.0.0"
```

### Authentication Issues

**Problem:** 401 Unauthorized
- Check API key is correct
- Check OAuth2 token hasn't expired (30 min)

**Problem:** 403 Forbidden
- Check user has PTI, ADMIN, or APTI role
- Check user account is active

### Database Issues

**Problem:** Connection refused
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U your_user -d warriorfit_test
```

---

## License

Copyright (c) 2025 Goethals Benoit

This source code is provided for viewing purposes only.

You may NOT:
- Use this code in any project
- Copy, modify, or distribute this code
- Use this code for commercial or non-commercial purposes

All rights reserved.

---

## Support

For issues, questions, or contributions, please contact the project maintainer.

**Documentation:**
- [API Client Testing Guide](README_API_CLIENT.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Argon2 Specification](https://github.com/P-H-C/phc-winner-argon2)

**Version:** 1.0.0
**Last Updated:** 2026-02-07
