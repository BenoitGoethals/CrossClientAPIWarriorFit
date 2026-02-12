# WarriorFit API Test Client

This directory contains test clients for the WarriorFit API.

## Quick Start

### 1. Start the Server

```bash
# From project root
export PYTHONPATH=.
uv run python src/main.py
```

Server will start on: `https://localhost:8555`

### 2. Run Tests

#### Option A: Python Client (Recommended)

**Automated tests:**
```bash
uv run python test_api_client.py
```

**Interactive mode:**
```bash
uv run python test_api_client.py --interactive
```

#### Option B: Bash Script (curl)

```bash
./test_api.sh
```

## Authentication Methods

### 1. API Key (Full Access)

**Header:**
```bash
X-API-Key: warriorfit_cross_the_world
```

**Example:**
```bash
curl -X GET "https://localhost:8555/crosses" \
  -H "X-API-Key: warriorfit_cross_the_world" \
  --cacert ./src/certs/cert.pem
```

### 2. OAuth2 (Username/Password)

**Step 1: Login**
```bash
curl -X POST "https://localhost:8555/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_user&password=your_pass" \
  --cacert ./src/certs/cert.pem
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
  --cacert ./src/certs/cert.pem
```

## Role-Based Access Control

Only users with these roles can access the API:
- **PTI** ✅
- **ADMIN** ✅
- **APTI** ✅

Other roles (USER, GUEST, PLANNER) will receive:
```json
{
  "detail": "Access denied. Required roles: PTI, ADMIN, APTI"
}
```

## API Endpoints

### GET /crosses
Get all crosses

**Response:**
```json
[
  {
    "id": 1,
    "datetime_start": "2026-02-07T10:00:00",
    "distance": 5000.0,
    "executed": false,
    "description": "Morning run",
    "runners": []
  }
]
```

### GET /crosses/{id}
Get specific cross by ID

### GET /crosses/runners/{cross_id}
Get all runners for a cross

### POST /crosses/{cross_id}
Save cross recordings

**Request body:**
```json
[
  {
    "serial_number": "RUNNER001",
    "running_time": 125.5
  },
  {
    "serial_number": "RUNNER002",
    "running_time": 132.3
  }
]
```

## Python Client Usage

```python
from test_api_client import WarriorFitClient

# Initialize client
client = WarriorFitClient(
    base_url="https://localhost:8555",
    cert_path="./src/certs/cert.pem"
)

# Method 1: API Key
client.set_api_key("warriorfit_cross_the_world")
crosses = client.get_crosses()

# Method 2: OAuth2
client.login("username", "password")
crosses = client.get_crosses()

# Get specific cross
cross = client.get_cross(cross_id=1)

# Get runners
runners = client.get_runners(cross_id=1)

# Save recordings
recordings = [
    {"serial_number": "TEST001", "running_time": 125.5},
    {"serial_number": "TEST002", "running_time": 132.3}
]
result = client.save_recordings(cross_id=1, recordings=recordings)
```

## Testing Scenarios

### Test 1: API Key Authentication ✅
```bash
# Should succeed - API key has full access
curl -X GET "https://localhost:8555/crosses" \
  -H "X-API-Key: warriorfit_cross_the_world" \
  --cacert ./src/certs/cert.pem
```

### Test 2: OAuth2 with Authorized Role ✅
```bash
# User with PTI/ADMIN/APTI role - should succeed
# Login first, then use token
```

### Test 3: OAuth2 with Unauthorized Role ❌
```bash
# User with USER/GUEST role - should fail with 403
# Expected: "Access denied. Required roles: PTI, ADMIN, APTI"
```

### Test 4: No Authentication ❌
```bash
# Should fail with 401 Unauthorized
curl -X GET "https://localhost:8555/crosses" \
  --cacert ./src/certs/cert.pem
```

## SSL Certificate

The API uses a self-signed certificate located at:
- **Certificate**: `./src/certs/cert.pem`
- **Private Key**: `./src/certs/key.pem`

**Valid for:** 365 days
**Subject:** CN=localhost
**SANs:** localhost, *.localhost, 127.0.0.1, 0.0.0.0

### Verify Certificate
```bash
openssl s_client -connect localhost:8555 -showcerts
```

## Troubleshooting

### SSL Certificate Errors
If you get SSL errors, use `--cacert` flag or set `verify=False` in Python:
```python
client = WarriorFitClient(base_url="https://localhost:8555", cert_path=None)
```

### 401 Unauthorized
- Check API key is correct
- Check OAuth2 token hasn't expired (30 min lifetime)

### 403 Forbidden
- Check user has PTI, ADMIN, or APTI role
- Check user account is active (`is_active=True`)

### Connection Refused
- Ensure server is running: `uv run python src/main.py`
- Check port 8555 is available
- Check firewall settings

## Configuration

Edit `src/config/config.yml`:

```yaml
api:
  secret_key: warriorfit_cross_the_world           # API Key
  oauth2_secret_key: warriorfit_oauth2_jwt_secret_key_change_in_production
  algorithm: HS256
  access_token_expire_minutes: 30
```

## Security Features

✅ **Argon2id password hashing** - Stronger than bcrypt
✅ **Role-based access control** - PTI/ADMIN/APTI only
✅ **JWT tokens** - Signed with HS256
✅ **SSL/TLS** - Self-signed certificate
✅ **Certificate validation** - Automatic on startup
✅ **Token expiration** - 30 minutes
✅ **Password migration** - Auto-upgrades bcrypt → Argon2

---

**Created:** 2026-02-07
**Author:** Claude + Benoit
**Version:** 1.0.0
