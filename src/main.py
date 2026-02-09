import logging
from typing import List
from pathlib import Path
from datetime import timedelta

from starlette.responses import RedirectResponse

from src.data.model.db_model import Runner
from src.data.model.schemas import CrossResponse, RunnerResponse, RunnerCreate, Token

from src.data.repo.cross_repository import CrossRepository
from src.core.config_reader import get_config

from fastapi import FastAPI, Security, HTTPException, status, Request, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.core.oauth2 import authenticate_user, create_access_token, get_current_user

app = FastAPI(
    title="WarriorFit API",
    description="API for accessing the WarriorFit running event database",
    version="1.0.1",
    docs_url = "/docs" ,
    port = 8550
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("../app.log"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger(__name__)


def validate_ssl_certificates(cert_path: str, key_path: str) -> dict:
    """
    Validate SSL certificates before starting the server.

    Checks:
    - Certificate and key files exist
    - Certificate is not expired
    - Certificate and key match
    - Files are readable

    :param cert_path: Path to certificate file
    :param key_path: Path to private key file
    :return: Dict with validation results
    :raises SystemExit: If validation fails critically
    """
    import subprocess
    from datetime import datetime

    results = {
        "valid": True,
        "warnings": [],
        "errors": []
    }

    # Check if files exist
    cert_file = Path(cert_path)
    key_file = Path(key_path)

    if not cert_file.exists():
        results["errors"].append(f"Certificate file not found: {cert_path}")
        results["valid"] = False

    if not key_file.exists():
        results["errors"].append(f"Private key file not found: {key_path}")
        results["valid"] = False

    if not results["valid"]:
        return results

    # Check if files are readable
    try:
        with open(cert_path, 'r') as f:
            f.read(1)
    except Exception as e:
        results["errors"].append(f"Cannot read certificate file: {e}")
        results["valid"] = False

    try:
        with open(key_path, 'r') as f:
            f.read(1)
    except Exception as e:
        results["errors"].append(f"Cannot read private key file: {e}")
        results["valid"] = False

    if not results["valid"]:
        return results

    # Validate certificate expiry
    try:
        cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-enddate"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        expiry_str = result.stdout.strip().replace("notAfter=", "")
        expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")

        days_until_expiry = (expiry_date - datetime.now()).days

        if days_until_expiry < 0:
            results["errors"].append(f"Certificate EXPIRED {abs(days_until_expiry)} days ago!")
            results["valid"] = False
        elif days_until_expiry < 30:
            results["warnings"].append(f"Certificate expires in {days_until_expiry} days")
        else:
            logger.info(f"Certificate valid for {days_until_expiry} days")

    except subprocess.CalledProcessError as e:
        results["errors"].append(f"Failed to validate certificate expiry: {e}")
        results["valid"] = False
    except Exception as e:
        results["warnings"].append(f"Could not parse certificate expiry date: {e}")

    # Validate private key
    try:
        cmd = ["openssl", "rsa", "-in", key_path, "-check", "-noout"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Private key validation: OK")
    except subprocess.CalledProcessError as e:
        results["errors"].append(f"Private key validation failed: {e.stderr}")
        results["valid"] = False

    # Validate certificate and key match
    try:
        # Get certificate modulus
        cmd_cert = ["openssl", "x509", "-noout", "-modulus", "-in", cert_path]
        cert_result = subprocess.run(cmd_cert, capture_output=True, text=True, check=True)
        cert_modulus = cert_result.stdout.strip()

        # Get key modulus
        cmd_key = ["openssl", "rsa", "-noout", "-modulus", "-in", key_path]
        key_result = subprocess.run(cmd_key, capture_output=True, text=True, check=True)
        key_modulus = key_result.stdout.strip()

        if cert_modulus != key_modulus:
            results["errors"].append("Certificate and private key DO NOT MATCH!")
            results["valid"] = False
        else:
            logger.info("Certificate and private key: MATCH")

    except subprocess.CalledProcessError as e:
        results["errors"].append(f"Failed to verify certificate/key match: {e}")
        results["valid"] = False

    return results

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request body: {await request.body()}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(await request.body())}
    )

# API Key Security
config = get_config()
API_KEY = config.api.secret_key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return api_key


async def get_current_user_or_api_key(
    api_key: str = Security(api_key_header),
    user: dict = Depends(get_current_user)
):
    """
    Combined authentication: accepts either API Key or OAuth2 token.
    Tries API key first, falls back to OAuth2 token.
    """
    if api_key == API_KEY:
        return {"type": "api_key", "role": "API_KEY"}
    # If API key is invalid, check OAuth2 token
    return {"type": "oauth2", **user}


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control.

    Only users with specified roles (or API key) can access the endpoint.

    :param allowed_roles: List of allowed role names (e.g., ["PTI", "ADMIN", "APTI"])
    :return: Dependency function that verifies user role
    """
    async def role_checker(auth: dict = Depends(get_current_user_or_api_key)):
        # API keys bypass role checks
        if auth.get("type") == "api_key":
            return auth

        # Check if user is active
        if not auth.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Check user role
        user_role = auth.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )

        return auth

    return role_checker


repo = CrossRepository()


@app.on_event("startup")
async def startup_event():
    """
    Validate SSL certificates on application startup.

    This runs when uvicorn starts the app directly (without __main__).
    """
    import os

    # Check if running with SSL
    cert_path = os.environ.get("SSL_CERTFILE", "./src/certs/cert.pem")
    key_path = os.environ.get("SSL_KEYFILE", "./src/certs/key.pem")

    # Only validate if both files exist (SSL is being used)
    if Path(cert_path).exists() and Path(key_path).exists():
        logger.info("=" * 60)
        logger.info("Validating SSL certificates on startup...")
        validation = validate_ssl_certificates(cert_path, key_path)

        # Display warnings
        for warning in validation["warnings"]:
            logger.warning(f"⚠️  {warning}")

        # Display errors but don't stop (uvicorn will handle it)
        if not validation["valid"]:
            logger.error("SSL CERTIFICATE VALIDATION FAILED!")
            for error in validation["errors"]:
                logger.error(f"❌ {error}")
        else:
            logger.info("✅ SSL certificates validated successfully")

        logger.info("=" * 60)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint.

    Returns a JWT access token for authenticated users.
    """
    username = await authenticate_user(form_data.username, form_data.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=config.api.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Define allowed roles for API access
ALLOWED_ROLES = ["PTI", "ADMIN", "APTI"]

@app.get("/crosses", response_model=List[CrossResponse])
async def get_crosses(auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Get all crosses. Requires PTI, ADMIN, or APTI role."""
    return await repo.get_all_crosses()

@app.get("/crosses/{id_cross}", response_model=CrossResponse)
async def get_cross(id_cross: int, auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Get a specific cross by ID. Requires PTI, ADMIN, or APTI role."""
    return await repo.get_cross(id_cross)

@app.post("/crosses/{serial_number}/{id_cross}")
async def add_runner(serial_number:str, id_cross:int, auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Add a runner to a cross. Requires PTI, ADMIN, or APTI role."""
    return await repo.add_runner(serial_number, id_cross)

@app.get("/crosses/runners/{cross_id}", response_model=List[RunnerResponse])
async def get_runners(cross_id: int, auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Get all runners for a cross. Requires PTI, ADMIN, or APTI role."""
    return await repo.get_all_runners(cross_id)

@app.post("/crosses/runner/{serial_number}/{id_cross}")
async def add_runner_duplicate(serial_number:str, id_cross:int, auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Add a runner to a cross (duplicate endpoint). Requires PTI, ADMIN, or APTI role."""
    return await repo.add_runner(serial_number, id_cross)

@app.post("/crosses/{cross_id}")
async def save_cross_recordings(cross_id: int, recordings: List[RunnerCreate], auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Save cross recordings. Requires PTI, ADMIN, or APTI role."""
    logger.info(f"Received POST request to /crosses/{cross_id}")
    logger.info(f"Number of recordings: {len(recordings)}")
    logger.info(f"Recordings data: {recordings}")

    runners: List[Runner] = []
    for recording in recordings:
        runners.append(Runner(running_time=recording.running_time, serial_number=recording.serial_number))

    return await repo.save_recordings(cross_id, runners)


if __name__ == "__main__":
    import uvicorn
    import sys
    import os

    # Get the project root directory (parent of src/)
    project_root = Path(__file__).parent.parent.absolute()

    # SSL certificate paths (handle both running from project root and from src/)
    cert_path = project_root / "src" / "certs" / "cert.pem"
    key_path = project_root / "src" / "certs" / "key.pem"

    logger.info(f"Looking for certificates at: {cert_path}")

    # Validate SSL certificates before starting
    logger.info("=" * 60)
    logger.info("Validating SSL certificates...")
    validation = validate_ssl_certificates(str(cert_path), str(key_path))

    # Display warnings
    for warning in validation["warnings"]:
        logger.warning(f"⚠️  {warning}")

    # Display errors and exit if invalid
    if not validation["valid"]:
        logger.error("=" * 60)
        logger.error("SSL CERTIFICATE VALIDATION FAILED!")
        for error in validation["errors"]:
            logger.error(f"❌ {error}")
        logger.error("=" * 60)
        logger.error("Server startup aborted due to invalid SSL certificates.")
        sys.exit(1)

    logger.info("✅ SSL certificates validated successfully")
    logger.info("=" * 60)

    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8555,
        ssl_keyfile=str(key_path),
        ssl_certfile=str(cert_path)
    )