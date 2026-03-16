# WarriorFit API - Security Documentation

A comprehensive overview of all security measures implemented in the WarriorFit FastAPI application, mapped against the **OWASP API Security Top 10 (2023)** and **OWASP Top 10 (2021)** frameworks.

---

## Table of Contents

- [Security Architecture Overview](#security-architecture-overview)
- [OWASP API Security Top 10 (2023) Compliance](#owasp-api-security-top-10-2023-compliance)
- [OWASP Top 10 (2021) Compliance](#owasp-top-10-2021-compliance)
- [1. Authentication](#1-authentication)
  - [1.1 OAuth2 Password Flow + JWT](#11-oauth2-password-flow--jwt)
  - [1.2 API Key Authentication](#12-api-key-authentication)
  - [1.3 Combined Authentication Flow](#13-combined-authentication-flow)
- [2. Authorization (RBAC)](#2-authorization-rbac)
- [3. Password Security](#3-password-security)
  - [3.1 Argon2id Hashing](#31-argon2id-hashing)
  - [3.2 Automatic bcrypt Migration](#32-automatic-bcrypt-migration)
  - [3.3 Fernet Password Support (User-Management Service)](#33-fernet-password-support-user-management-service)
- [4. Rate Limiting](#4-rate-limiting)
- [5. Input Validation](#5-input-validation)
- [6. SQL Injection Prevention](#6-sql-injection-prevention)
- [7. Transport Security (SSL/TLS)](#7-transport-security-ssltls)
- [8. CORS Policy](#8-cors-policy)
- [9. Error Handling & Information Disclosure](#9-error-handling--information-disclosure)
- [10. Logging & Auditing](#10-logging--auditing)
- [11. Credential Protection](#11-credential-protection)
- [12. Container Security](#12-container-security)
- [13. Middleware Stack](#13-middleware-stack)
- [14. Endpoint Security Matrix](#14-endpoint-security-matrix)
- [15. Dependencies & Supply Chain](#15-dependencies--supply-chain)
- [16. Recommendations](#16-recommendations)
- [References](#references)

---

## Security Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       Client Request                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  1. SSL/TLS Layer (HTTPS)                       │
│  RSA 4096-bit | SHA-256 | Certificate validated on startup     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              2. Rate Limiting (slowapi)                         │
│  IP-based | /token: 5 req/min | Brute-force protection         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              3. CORS Middleware                                  │
│  Cross-origin request filtering                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              4. Auth Failure Audit Middleware                    │
│  Logs 401/403 responses with client IP                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              5. Authentication Layer                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   X-API-Key Header                                        │  │
│  │   Present + valid   → ADMIN role                         │  │
│  │   Present + invalid → 403 FORBIDDEN                      │  │
│  │   Absent            → 403 FORBIDDEN                      │  │
│  └──────────────────────────────┬───────────────────────────┘  │
└──────────────────────────────────┼──────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              6. Authorization Layer (RBAC)                       │
│  Allowed roles: PTI, ADMIN, APTI                                │
│  Checks: role membership + is_active flag                       │
│  API key users: ADMIN role, subject to same checks              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              7. Input Validation                                │
│  Pydantic schemas | Path constraints | Server-side sanitization │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              8. Business Logic & Database                        │
│  SQLAlchemy ORM | Parameterized queries | Async sessions        │
└─────────────────────────────────────────────────────────────────┘
```

---

## OWASP API Security Top 10 (2023) Compliance

This section maps each OWASP API Security risk to the measures implemented in WarriorFit.

| # | OWASP Risk | Status | Implementation |
|---|------------|--------|----------------|
| API1 | Broken Object Level Authorization (BOLA) | Mitigated | RBAC enforced on all `/crosses/*` endpoints; users must have PTI/ADMIN/APTI role |
| API2 | Broken Authentication | Mitigated | JWT with expiry, Argon2id hashing, Fernet fallback, rate limiting on `/token`, API key required on all protected endpoints (no OAuth2 fallback) |
| API3 | Broken Object Property Level Authorization | Mitigated | Pydantic response models control which fields are serialized; ORM prevents mass assignment |
| API4 | Unrestricted Resource Consumption | Partially mitigated | Rate limiting on `/token` (5/min); other endpoints not yet rate-limited |
| API5 | Broken Function Level Authorization (BFLA) | Mitigated | `require_roles()` dependency factory enforces role checks on every protected endpoint |
| API6 | Unrestricted Access to Sensitive Business Flows | Partially mitigated | Rate limiting on login; bulk recording endpoint validates input |
| API7 | Server-Side Request Forgery (SSRF) | Not applicable | No user-supplied URLs are fetched server-side |
| API8 | Security Misconfiguration | Mostly mitigated | SSL validation on startup, structured config, middleware stack; CORS is permissive (see recommendations) |
| API9 | Improper Inventory Management | Mitigated | Single API version, `version.yaml` tracks version/commit; `/docs` and `/redoc` auto-document all endpoints |
| API10 | Unsafe Consumption of APIs | Not applicable | No third-party API consumption in current codebase |

---

## OWASP Top 10 (2021) Compliance

| # | OWASP Risk | Status | Implementation |
|---|------------|--------|----------------|
| A01 | Broken Access Control | Mitigated | RBAC with role whitelist, active-user check, API key no longer bypasses role checks |
| A02 | Cryptographic Failures | Mitigated | Argon2id password hashing, Fernet symmetric encryption fallback, RSA 4096-bit TLS, HS256 JWT signing, automatic bcrypt migration |
| A03 | Injection | Mitigated | SQLAlchemy parameterized queries, Pydantic input validation, server-side serial number sanitization |
| A04 | Insecure Design | Mitigated | Defense-in-depth (multi-layer security), fail-closed auth design, no silent fallback |
| A05 | Security Misconfiguration | Mostly mitigated | SSL auto-validation, structured config classes; CORS needs restriction for production |
| A06 | Vulnerable and Outdated Components | Mitigated | `uv.lock` for reproducible builds, modern dependency versions, `--frozen` flag in Docker |
| A07 | Identification and Authentication Failures | Mitigated | Argon2id, Fernet fallback, JWT expiry, rate limiting, credential masking in logs |
| A08 | Software and Data Integrity Failures | Mitigated | Locked dependencies (`uv.lock`), frozen config dataclasses, version tracking |
| A09 | Security Logging and Monitoring Failures | Mitigated | Dedicated auth logger, rotating log files, email alerts, audit middleware |
| A10 | Server-Side Request Forgery (SSRF) | Not applicable | No user-supplied URL fetching |

---

## 1. Authentication

### 1.1 OAuth2 Password Flow + JWT

**File**: `src/core/oauth2.py`

The application implements the OAuth2 Resource Owner Password Credentials flow:

1. Client sends `username` + `password` to `POST /token`
2. Server validates credentials against the database (Argon2id verification)
3. Server issues a signed JWT access token
4. Client includes token in `Authorization: Bearer <token>` header
5. Server validates token signature, expiry, and fetches user data from DB

**JWT Configuration:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Algorithm | HS256 (HMAC-SHA256) | Token signature algorithm |
| Expiration | 30 minutes | Limits window of token theft exploitation |
| Secret key | Configurable via `config.yml` | Signing key (must be changed in production) |
| Library | `python-jose[cryptography]` | JWT encoding/decoding |
| Claims | `sub` (username), `exp` (expiry) | Token payload |

**Token validation flow:**
```
Token received → Decode with secret key → Verify expiry
    → Extract username → Fetch user from DB → Return user dict
    → Any failure → 401 UNAUTHORIZED
```

### 1.2 API Key Authentication

**File**: `src/core/auth.py`

Static API key authentication via the `X-API-Key` HTTP header, intended for server-to-server communication.

**Key security properties:**

- **API key required**: All protected endpoints require a valid `X-API-Key` header. Requests without the header are rejected immediately with `403 FORBIDDEN`.
- **No silent fallback**: An invalid key is rejected with `403 FORBIDDEN`; the server never falls back to another auth mechanism.
- **Role assignment**: API key authenticated requests receive the `ADMIN` role and are subject to the same RBAC checks as all other requests.
- **Credential masking**: Invalid API key attempts are logged with only the last 4 characters visible (`****abcd`).

```python
# Fail-closed design — API key required; no OAuth2 fallback
if api_key is not None:
    if api_key == API_KEY:
        return {"type": "api_key", "role": API_KEY_ROLE}  # ADMIN
    # Header present but invalid — reject immediately
    auth_logger.warning("Invalid API key attempted: %s", _mask_key(api_key))
    raise HTTPException(status_code=403, detail="Invalid API Key")

# No header present — also rejected
auth_logger.warning("Invalid API key attempted: %s", _mask_key(api_key))
raise HTTPException(status_code=403, detail="Invalid or missing API Key")
```

### 1.3 Authentication Flow

All protected endpoints require a valid API key. There is no OAuth2 fallback for the `get_current_user_or_api_key` dependency.

```
Request arrives
    │
    ├── X-API-Key header present?
    │       ├── YES, key valid    → Authenticated as ADMIN (api_key)
    │       └── YES, key invalid  → 403 FORBIDDEN
    │
    └── No X-API-Key header → 403 FORBIDDEN "Invalid or missing API Key"
```

**OWASP relevance:**
- **API2:2023 (Broken Authentication)**: Fail-closed design prevents auth bypass via header manipulation; missing key is treated as a failure, not a fallback trigger.
- **A07:2021 (Identification and Authentication Failures)**: No default credentials accepted at runtime; absent or invalid keys are rejected and logged.

---

## 2. Authorization (RBAC)

**File**: `src/core/auth.py` — `require_roles()` dependency factory

Role-Based Access Control is enforced on every protected endpoint through a FastAPI dependency injection pattern.

### Role Definitions

**File**: `src/data/model/role.py`

| Role | Enum Value | API Access |
|------|------------|------------|
| `ADMIN` | `"ADMIN"` | Allowed |
| `PTI` | `"PTI"` | Allowed |
| `APTI` | `"APTI"` | Allowed |
| `USER` | `"USER"` | Denied |
| `GUEST` | `"GUEST"` | Denied |
| `PLANNER` | `"PLANNER"` | Denied |

### Enforcement Flow

```
Authenticated request
    │
    ├── Is user active? (OAuth2 users only)
    │       └── NO → 403 "User account is inactive"
    │
    └── Is role in allowed list [PTI, ADMIN, APTI]?
            ├── YES → Access granted
            └── NO  → 403 "Access denied. Required roles: PTI, ADMIN, APTI"
```

**Key design decision**: API key authenticated requests are assigned the `ADMIN` role and pass through the same role check — they do **not** bypass RBAC. This ensures a single, consistent authorization path for all request types.

**OWASP relevance:**
- **API1:2023 (BOLA)**: All object access requires authenticated + authorized user.
- **API5:2023 (BFLA)**: Every endpoint uses `require_roles()` — no unprotected admin functions.
- **A01:2021 (Broken Access Control)**: Centralized role enforcement, deny-by-default.

---

## 3. Password Security

### 3.1 Argon2id Hashing

**File**: `src/core/oauth2.py`

Argon2id is the winner of the Password Hashing Competition (2015) and is recommended by OWASP for password storage.

**Configuration:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Algorithm | Argon2id (hybrid mode) | Combines Argon2i (side-channel resistant) and Argon2d (GPU-resistant) |
| Time cost | 2 iterations | Computational cost |
| Memory cost | 102,400 KiB (100 MiB) | Memory-hardness (prevents GPU/ASIC attacks) |
| Parallelism | 8 threads | CPU lane parallelism |
| Hash length | 16 bytes | Output hash size |
| Salt length | 16 bytes | Auto-generated per hash |
| Library | `argon2-cffi` v23.1.0+ | Python binding for the reference C implementation |

**Why Argon2id over alternatives:**

| Algorithm | Memory Usage | GPU/ASIC Resistant | Side-Channel Resistant | Status |
|-----------|-------------|-------------------|----------------------|--------|
| **Argon2id** | 100 MiB | Strong | Yes | **Active (primary)** |
| bcrypt | ~4 KiB | Moderate | No | Legacy (migration) |
| PBKDF2 | Minimal | Weak | No | Not used |
| scrypt | Configurable | Good | No | Not used |

### 3.2 Automatic bcrypt Migration

Users with legacy bcrypt-hashed passwords are seamlessly upgraded to Argon2id on their next successful login:

```
Login request (username + password)
    │
    ├── Hash starts with "$argon2"?
    │       └── Verify with Argon2id
    │           ├── Valid + needs_rehash → Rehash with current params, update DB
    │           ├── Valid              → Proceed
    │           └── Invalid            → 401
    │
    ├── Hash starts with "$2b$" / "$2a$" / "$2y$"?
    │       └── Verify with bcrypt
    │           ├── Valid → Rehash with Argon2id, update DB, proceed
    │           └── Invalid → 401
    │
    └── Otherwise → attempt Fernet decryption (see §3.3)
```

**Password never stored in plaintext** — only the hash/token is persisted. The migration is transparent to the user.

**OWASP relevance:**
- **A02:2021 (Cryptographic Failures)**: Uses the strongest available password hashing algorithm with memory-hard parameters.
- **API2:2023 (Broken Authentication)**: No weak hashing, no plaintext storage, automatic upgrade path.

### 3.3 Fernet Password Support (User-Management Service)

**File**: `src/core/oauth2.py`

Passwords created by the external **user-management service** are stored as [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption tokens rather than hashes. The CrossClientAPI supports these tokens as a third verification path during login.

**Key derivation:**

| Step | Operation |
|------|-----------|
| 1 | Read `WF_SECRET_KEY` from environment (loaded from `.env` via `python-dotenv`) |
| 2 | `SHA-256(WF_SECRET_KEY)` → 32-byte digest |
| 3 | `base64url(digest)` → valid Fernet key |

**Verification flow:**

```
Stored token does not match Argon2 or bcrypt format
    │
    └── Try Fernet decrypt(token, derived_key)
            ├── Decrypted == plain_password → Valid, no rehash needed
            └── InvalidToken / any error   → 401
```

> **Note**: Fernet is symmetric encryption, not a one-way hash. The key is derived at startup from `WF_SECRET_KEY`. A compromised key means stored tokens can be decrypted. Rotate `WF_SECRET_KEY` if it is ever exposed.

**OWASP relevance:**
- **API2:2023 (Broken Authentication)**: Interoperability with the user-management service without weakening the primary Argon2id path.
- **A02:2021 (Cryptographic Failures)**: Key is derived with SHA-256 and never stored or logged.

---

## 4. Rate Limiting

**Files**: `src/core/rate_limiter.py`, `src/main.py`

Rate limiting is implemented using `slowapi`, a library built on `limits` and integrated with FastAPI/Starlette.

### Configuration

| Parameter | Value |
|-----------|-------|
| Library | `slowapi` v0.1.9+ |
| Key function | `get_remote_address()` (client IP) |
| Backend | In-memory (default) |
| Middleware | `SlowAPIMiddleware` |

### Applied Limits

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /token` | 5 requests/minute | Prevents brute-force password attacks and credential stuffing |

When a rate limit is exceeded, the server returns **HTTP 429 Too Many Requests** with a `Retry-After` header.

**OWASP relevance:**
- **API4:2023 (Unrestricted Resource Consumption)**: Rate limiting on the authentication endpoint prevents brute-force and credential stuffing attacks.
- **API2:2023 (Broken Authentication)**: Login rate limiting significantly slows down automated attacks.

---

## 5. Input Validation

Input validation is implemented at multiple layers: FastAPI path parameters, Pydantic schemas, and explicit server-side checks.

### 5.1 Path Parameter Validation

**File**: `src/main.py`

| Parameter | Type | Constraints |
|-----------|------|-------------|
| `id_cross` | `int` | `gt=0` (must be positive) |
| `cross_id` | `int` | `gt=-1` (non-negative) or `gt=0` |
| `serial_number` | `str` | `min_length=1`, `max_length=10` |

### 5.2 Server-Side Serial Number Sanitization

Beyond Pydantic/path validation, serial numbers undergo explicit server-side sanitization:

```python
serial_number_clean = serial_number.strip()
if not serial_number_clean:
    raise HTTPException(400, "Serial number cannot be empty")
if not serial_number_clean.replace('-', '').replace('_', '').isalnum():
    raise HTTPException(400, "Serial number contains invalid characters")
```

**Allowed characters**: `a-z`, `A-Z`, `0-9`, `-`, `_`

This prevents injection of special characters (SQL, shell, or otherwise) through the serial number field.

### 5.3 Pydantic Schema Validation

**File**: `src/data/model/schemas.py`

- **Response models** (`RunnerResponse`, `CrossResponse`): Control exactly which fields are serialized to JSON, preventing accidental exposure of internal fields (e.g., password hashes).
- **Request models** (`RunnerCreate`, `CrossCreate`): Enforce type constraints on request bodies.
- **`from_attributes=True`**: Enables ORM-to-schema conversion without exposing raw database objects.

### 5.4 Recordings Validation

Bulk recording submissions undergo per-item validation:

```python
for i, recording in enumerate(recordings):
    if recording.running_time < 0:
        raise HTTPException(400, f"Invalid running time at index {i}")
```

### 5.5 Request Validation Error Handler

**File**: `src/main.py`

A custom exception handler for `RequestValidationError` provides:
- Structured error response (422 status code)
- Logging of validation failures (with truncated body preview, max 4,096 bytes)
- Auth-related validation errors routed to the dedicated `auth_logger`
- Safe body decoding with `errors="replace"` to prevent crash on malformed input

**OWASP relevance:**
- **A03:2021 (Injection)**: Multi-layer input validation blocks injection vectors at the earliest possible point.
- **API3:2023 (Broken Object Property Level Authorization)**: Pydantic schemas prevent mass assignment and excessive data exposure.

---

## 6. SQL Injection Prevention

**File**: `src/data/repo/cross_repository.py`

All database operations use SQLAlchemy's ORM with parameterized queries. **No raw SQL with string interpolation is used anywhere in the codebase.**

### Parameterized Query Examples

```python
# User lookup — username is a bound parameter, not interpolated
stmt = select(User).where(User.username == username)

# Cross lookup — id_cross is a bound parameter
stmt = select(Cross).where(Cross.id == id_cross)

# Runner lookup with eager loading
stmt = select(Cross).options(selectinload(Cross.runners)).where(Cross.id == cross_id)
```

### Defense-in-Depth

SQL injection is prevented at three layers:

1. **Input validation** (Pydantic + path constraints): Rejects malformed input before it reaches the database layer.
2. **ORM parameterization** (SQLAlchemy): All user input is automatically escaped and quoted as bound parameters.
3. **Type safety** (Python typing + FastAPI): Path parameters are typed as `int` or constrained `str`, preventing type-confusion attacks.

**OWASP relevance:**
- **A03:2021 (Injection)**: Parameterized queries are the primary defense against SQL injection per OWASP guidelines.

---

## 7. Transport Security (SSL/TLS)

**File**: `src/core/ssl_validator.py`

All communication is encrypted over HTTPS using self-signed certificates.

### Certificate Specifications

| Parameter | Value |
|-----------|-------|
| Algorithm | RSA 4096-bit |
| Signature | SHA-256 |
| Validity | 365 days |
| Format | PEM |
| Location | `src/certs/cert.pem` and `src/certs/key.pem` |
| SANs | `localhost`, `*.localhost`, `127.0.0.1`, `0.0.0.0` |

### Pre-Startup Validation

The application performs **6 automated checks** before accepting any traffic:

| # | Check | Failure Behavior |
|---|-------|-----------------|
| 1 | Certificate file exists and is readable | Error — startup aborted |
| 2 | Private key file exists and is readable | Error — startup aborted |
| 3 | Certificate is not expired | Error — startup aborted |
| 4 | Certificate expiry within 30 days | Warning — startup continues |
| 5 | Private key is valid (RSA format check via OpenSSL) | Error — startup aborted |
| 6 | Certificate and key modulus match | Error — startup aborted |

### Environment Variable Overrides

| Variable | Purpose |
|----------|---------|
| `SSL_CERTFILE` | Override certificate path |
| `SSL_KEYFILE` | Override private key path |

**OWASP relevance:**
- **A02:2021 (Cryptographic Failures)**: RSA 4096-bit encryption with automated validation prevents expired or mismatched certificates from being used.
- **API8:2023 (Security Misconfiguration)**: Startup validation catches certificate issues before the API becomes accessible.

---

## 8. CORS Policy

**File**: `src/main.py`

Cross-Origin Resource Sharing is configured via FastAPI's `CORSMiddleware`:

| Setting | Value | Notes |
|---------|-------|-------|
| `allow_origins` | `["*"]` | All origins allowed |
| `allow_credentials` | `True` | Cookies/auth headers allowed cross-origin |
| `allow_methods` | `["*"]` | All HTTP methods |
| `allow_headers` | `["*"]` | All headers |

> **Note**: The current CORS configuration is permissive for development. See [Recommendations](#16-recommendations) for production hardening.

**OWASP relevance:**
- **API8:2023 (Security Misconfiguration)**: Overly permissive CORS is a known misconfiguration risk. The current setting should be restricted before production deployment.

---

## 9. Error Handling & Information Disclosure

The application follows the principle of **minimal information disclosure**: clients receive generic error messages while detailed context is logged server-side.

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Error description (generic, safe for clients)"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 400 | Bad Request | Invalid input (empty serial number, negative time, empty recordings) |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Invalid API key, insufficient role, inactive account |
| 404 | Not Found | Cross/resource does not exist |
| 422 | Unprocessable Entity | Pydantic validation failure |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Database or unexpected errors |

### Information Disclosure Prevention

- **Database errors**: Generic `"Internal server error"` to client; full stack trace in server logs (`exc_info=True`).
- **Auth failures**: Generic `"Could not validate credentials"` — does not reveal whether the username or password was wrong.
- **Validation errors**: Return Pydantic validation details (field name, constraint violated) but no internal implementation details.
- **API key rejection**: Returns `"Invalid API Key"` without revealing the expected key format or length.

**OWASP relevance:**
- **API8:2023 (Security Misconfiguration)**: Generic error messages prevent information leakage that could help attackers.

---

## 10. Logging & Auditing

**File**: `src/core/logging_config.py`

### Logging Architecture

```
┌─────────────────────────────────────────────────┐
│                Application Events                │
│                                                  │
│  ┌──────────────┐      ┌──────────────────────┐ │
│  │  Main Logger  │      │  Auth Logger         │ │
│  │  ("app")      │      │  ("auth")            │ │
│  └──────┬───────┘      └──────────┬───────────┘ │
│         │                          │              │
│    ┌────┴────┐              ┌─────┴─────┐       │
│    ▼         ▼              ▼           ▼       │
│ Console   app.log       auth.log    SMTP Alert  │
│ (stdout)  (rotating)   (rotating)  (optional)   │
└─────────────────────────────────────────────────┘
```

### Main Application Logger

| Setting | Value |
|---------|-------|
| Output | Console (stdout) + `app.log` |
| Rotation | 5 MB max, 3 backups |
| Level | INFO |
| Format | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` |

### Dedicated Auth Logger

A **separate** logger exclusively for authentication and authorization events, isolated from general application logs for easier security auditing.

| Setting | Value |
|---------|-------|
| Output | `auth.log` only (no propagation) |
| Rotation | 5 MB max, 3 backups |
| Level | INFO |

**Events logged to `auth.log`:**

| Event | Log Level | Example Message |
|-------|-----------|-----------------|
| Invalid login attempt | WARNING | `Invalid login attempt for user: john` |
| Invalid password | WARNING | `Invalid password for user: john` |
| Invalid API key | WARNING | `Invalid API key attempted: ****abcd` |
| Role denied | WARNING | `Role USER not in allowed roles ['PTI', 'ADMIN', 'APTI']` |
| Inactive user | WARNING | `User account is inactive` |
| Token validation failure | WARNING | `Could not validate credentials` |
| Auth failure (middleware) | WARNING | `Auth failure: 403 POST /crosses client=192.168.1.5` |

### Auth Failure Audit Middleware

**File**: `src/main.py` — `AuthFailureAuditMiddleware`

A custom middleware that intercepts **all** responses and logs authentication/authorization failures:

- Triggers on **401** and **403** status codes
- Logs: status code, HTTP method, path, client IP
- **Excludes** noisy public endpoints: `/`, `/docs`, `/openapi.json`, `/redoc`

### Email Alerting (Optional)

A custom `SmtpHandler` can send email alerts for WARNING-level and above auth events:

| Setting | Value |
|---------|-------|
| Protocol | SMTP with optional TLS/SSL |
| Trigger level | WARNING |
| Timeout | 10 seconds |
| Error handling | Graceful (no crash on SMTP failure) |

**OWASP relevance:**
- **A09:2021 (Security Logging and Monitoring Failures)**: Dedicated auth logger, audit middleware, rotating logs, and optional email alerts provide comprehensive monitoring.

---

## 11. Credential Protection

### API Key Masking in Logs

**File**: `src/core/auth.py` — `_mask_key()`

API keys are **never** logged in full. The masking function reveals only the last 4 characters:

| Input | Logged As |
|-------|-----------|
| `warriorfit_cross_the_world` | `****orld` |
| `abc` | `****` |
| `None` / empty | `<empty>` |

### Password Protection in Logs

**File**: `src/core/oauth2.py`

- Passwords are **never** logged (a previous vulnerability that logged plaintext passwords has been fixed).
- Only the username is logged on failed authentication: `"Invalid password for user: %s", username`
- Log messages use `%s` formatting (not f-strings) to prevent accidental evaluation of user input.

### Configuration Secrets

Sensitive configuration values are loaded from `config.yml` and from `.env` (via `python-dotenv`, loaded in `config_reader.py` at startup), stored in typed dataclass instances:

| Secret | Source | Notes |
|--------|--------|-------|
| API key | `config.yml` → `config.api.secret_key` | Should be rotated regularly |
| JWT signing key | `config.yml` → `config.api.oauth2_secret_key` | Must be changed from default |
| DB password | `config.yml` → `config.database.password` | Per-environment config |
| SMTP password | `config.yml` → `config.mail.password` | Optional |
| Fernet key material | `.env` → `WF_SECRET_KEY` env var | Shared with user-management service; injected at runtime, never baked into the image |

### Frozen Configuration

`MailConfig` uses `@dataclass(frozen=True)`, making it immutable at runtime and preventing accidental modification of credentials.

---

## 12. Container Security

**File**: `Dockerfile`

| Measure | Implementation |
|---------|---------------|
| Minimal base image | `python:3.13-slim` (reduced attack surface) |
| Locked dependencies | `uv sync --frozen` (reproducible, tamper-evident builds) |
| Non-interactive build | No shell or debug tools in final image |
| Bytecode compilation | `UV_COMPILE_BYTECODE=1` (faster startup, no `.py` source needed at runtime) |
| Unbuffered output | `PYTHONUNBUFFERED=1` (real-time log visibility) |
| SSL in container | Certificates included; Uvicorn runs with `--ssl-keyfile` and `--ssl-certfile` |
| External config mount | Production config mounted at `/etc/CrossClientAPI/config.yml` |

### Deployment Script

**File**: `deploy.sh`

Automated deployment script with clean container lifecycle:

1. Resolve `WF_SECRET_KEY` — reads from the environment or falls back to parsing `.env`; **aborts with an error if not set**
2. Stop existing container
3. Remove existing container
4. Build new image
5. Run new container with restart policy (`--restart unless-stopped`)
6. External config volume mount (secrets not baked into image)
7. `WF_SECRET_KEY` injected at runtime via `-e "WF_SECRET_KEY=..."` (never embedded in the image layer)

---

## 13. Middleware Stack

Middleware executes in the **reverse** order of registration. The effective processing order for an incoming request is:

| Order | Middleware | Purpose |
|-------|-----------|---------|
| 1 | `SlowAPIMiddleware` | Rate limiting enforcement |
| 2 | `CORSMiddleware` | Cross-origin request handling |
| 3 | `AuthFailureAuditMiddleware` | Logging 401/403 responses |

---

## 14. Endpoint Security Matrix

| Endpoint | Method | Authentication | Authorization | Rate Limit | Input Validation |
|----------|--------|---------------|---------------|------------|-----------------|
| `/` | GET | None | None | None | None |
| `/docs` | GET | None | None | None | None |
| `/redoc` | GET | None | None | None | None |
| `/token` | POST | Credentials | None | **5/min** | Username/password form |
| `/crosses` | GET | API Key | PTI, ADMIN, APTI | None | None |
| `/crosses/{id_cross}` | GET | API Key | PTI, ADMIN, APTI | None | `id_cross > 0` |
| `/crosses/{serial}/{id_cross}` | POST | API Key | PTI, ADMIN, APTI | None | Serial: 1-10 chars, alphanumeric/-/_ ; `id_cross > 0` |
| `/crosses/runners/{cross_id}` | GET | API Key | PTI, ADMIN, APTI | None | `cross_id > 0` |
| `/crosses/runner/{serial}/{id_cross}` | POST | API Key | PTI, ADMIN, APTI | None | Serial: 1-10 chars, alphanumeric/-/_ ; `id_cross > 0` |
| `/crosses/{cross_id}` | POST | API Key | PTI, ADMIN, APTI | None | `cross_id >= 0`, running_time >= 0, non-empty list |

---

## 15. Dependencies & Supply Chain

**File**: `pyproject.toml`

| Dependency | Version | Security Role |
|------------|---------|--------------|
| `argon2-cffi` | >= 23.1.0 | Argon2id password hashing |
| `bcrypt` | >= 5.0.0 | Legacy password verification + migration |
| `python-jose[cryptography]` | >= 3.3.0 | JWT token signing and verification |
| `fastapi` | >= 0.124.0 | Framework with built-in security utilities |
| `uvicorn` | >= 0.38.0 | ASGI server with SSL/TLS support |
| `sqlalchemy[all,asyncio]` | >= 2.0.44 | ORM with parameterized query protection |
| `slowapi` | >= 0.1.9 | Rate limiting middleware |
| `asyncpg[all]` | >= 0.31.0 | Async PostgreSQL driver |
| `cryptography` | >= 44.0.0 | Low-level cryptographic operations; provides Fernet |
| `python-dotenv` | >= 1.0.0 | Loads `WF_SECRET_KEY` and other secrets from `.env` at startup |

**Supply chain protections:**
- `uv.lock` file locks exact dependency versions (reproducible builds)
- Docker builds use `--frozen` flag (fails if lock file is out of date)
- No `pip install` from arbitrary sources

**OWASP relevance:**
- **A06:2021 (Vulnerable and Outdated Components)**: Locked dependencies with version constraints reduce the risk of using vulnerable packages.
- **A08:2021 (Software and Data Integrity Failures)**: Lock file ensures builds are deterministic and tamper-evident.

---

## 16. Recommendations

Areas for further hardening before production deployment:

| Priority | Area | Current State | Recommendation |
|----------|------|---------------|----------------|
| **High** | CORS | `allow_origins=["*"]` | Restrict to specific trusted domains |
| **High** | Secrets | Config file with defaults | Use environment variables or a secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager) |
| **High** | Default credentials | Default API key and JWT secret in config | Enforce strong, unique secrets; fail startup if defaults detected |
| **Medium** | Rate limiting | Only on `/token` | Add per-endpoint limits on all mutation endpoints (POST) |
| **Medium** | SQL logging | `echo=True` on DB engine | Set `echo=False` in production to avoid logging query details |
| **Medium** | HTTPS | Self-signed certificates | Use trusted CA certificates (Let's Encrypt) for production |
| **Low** | JWT algorithm | HS256 (symmetric) | Consider RS256 (asymmetric) for multi-service architectures |
| **Low** | Token refresh | No refresh token mechanism | Implement refresh tokens for better UX without extending access token lifetime |
| **High** | Fernet key exposure | `WF_SECRET_KEY` allows token decryption | Rotate `WF_SECRET_KEY` immediately if exposed; treat it as a primary secret |
| **Low** | Account lockout | Not implemented | Lock accounts after N failed login attempts |
| **Low** | HSTS | Not set | Add `Strict-Transport-Security` header |

---

## References

- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [OWASP Top 10 (2021)](https://owasp.org/Top10/2021/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
- [Argon2 Specification (PHC Winner)](https://github.com/P-H-C/phc-winner-argon2)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

---

**Version:** 0.0.23
**Last Updated:** 2026-03-16
