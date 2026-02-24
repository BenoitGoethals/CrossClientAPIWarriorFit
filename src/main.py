"""WarriorFit API - FastAPI application for running event management."""
import logging
from typing import List, Annotated
from datetime import timedelta
from starlette.responses import RedirectResponse, HTMLResponse
from sqlalchemy.exc import SQLAlchemyError
from src.data.model.db_model import Runner
from src.data.model.schemas import CrossResponse, RunnerResponse, RunnerCreate, Token
from src.data.repo.cross_repository import CrossRepository
from src.core.dependencies import get_cross_repository
from src.core.config_reader import get_config
from src.core.logging_config import setup_logging
from src.core.lifespan import lifespan
from src.core.auth import require_roles
from src.core.oauth2 import authenticate_user, create_access_token
from src.core.version_loader import load_version
from fastapi import FastAPI, HTTPException, status, Request, Depends, Path
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.rate_limiter import limiter

# Configuration (load first so logging can use mail config)
config = get_config()

setup_logging(config.mail)
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger("auth")

# FastAPI application
app = FastAPI(
    title="WarriorFit API",
    description="API for accessing the WarriorFit running event database",
    version=load_version(),
    docs_url="/frago",
    redoc_url="/fragore",
    port=8550,
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class AuthFailureAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Skip noisy public endpoints
        public_paths = {"/", "/docs", "/openapi.json", "/redoc"}
        path = request.url.path

        if path not in public_paths and response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            client_host = request.client.host if request.client else "<unknown>"
            auth_logger.warning(
                "Auth failed: status=%s method=%s path=%s client=%s",
                response.status_code,
                request.method,
                path,
                client_host,
            )

        return response

app.add_middleware(AuthFailureAuditMiddleware)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("Validation error for %s %s", request.method, request.url)

    cached = getattr(request.state, "cached_body", b"")
    # Keep logs safe + readable (don’t crash on decoding issues, don’t dump huge bodies)
    body_preview = cached[:4096].decode("utf-8", errors="replace") if cached else ""

    # Auth-related validation errors (e.g. malformed /token requests) should go to auth_logger
    if request.url.path == "/token":
        auth_logger.warning(
            "Auth request validation error for %s %s | errors=%s | body_preview=%s",
            request.method,
            request.url,
            exc.errors(),
            body_preview,
        )
    else:
        logger.error("Validation error for %s %s", request.method, request.url)
        logger.error("Request body (preview): %s", body_preview)
        logger.error("Validation errors: %s", exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body_preview},
    )

# Define allowed roles for API access
ALLOWED_ROLES = ["PTI", "ADMIN", "APTI"]

html_page = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Belgium Cross Team</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
    body {
        margin:0;
        font-family: Arial, Helvetica, sans-serif;
        background: linear-gradient(135deg,#000000,#222);
        color:white;
        text-align:center;
    }

    .hero {
        padding:80px 20px;
        background: linear-gradient(90deg, #000000, #ff0000, #ffd000);
    }

    h1 {
        font-size:60px;
        margin:0;
        letter-spacing:2px;
    }

    h2 {
        font-weight:300;
        margin-top:10px;
    }

    .section {
        padding:60px 20px;
        max-width:900px;
        margin:auto;
    }

    .cards {
        display:flex;
        flex-wrap:wrap;
        justify-content:center;
        gap:25px;
        margin-top:30px;
    }

    .card {
        background:#111;
        border-radius:15px;
        padding:25px;
        width:250px;
        box-shadow:0 0 20px rgba(255,0,0,0.4);
    }

    .cta {
        background:#ff0000;
        padding:20px 40px;
        font-size:22px;
        border-radius:50px;
        text-decoration:none;
        color:white;
        display:inline-block;
        margin-top:30px;
        transition:0.3s;
    }

    .cta:hover {
        background:#ffd000;
        color:black;
    }

    footer {
        padding:40px;
        background:#000;
        font-size:14px;
        opacity:0.8;
    }
</style>
</head>

<body>

<div class="hero">
    <h1>🇧🇪 BELGIUM CROSS TEAM</h1>
    <h2>Stronger Together • Faster Together • Fearless Together</h2>
</div>

<div class="section">
    <h2>Join the Elite Endurance Community</h2>
    <p>
        Runners • Hikers • Mountainbikers • Fitness Warriors  
        We train, compete and push limits together across Belgium.
    </p>

    <div class="cards">
        <div class="card">
            <h3>🏃 Running</h3>
            <p>Weekly group runs and race preparation programs.</p>
        </div>

        <div class="card">
            <h3>🚵 MTB</h3>
            <p>Trail rides, technical coaching and endurance rides.</p>
        </div>

        <div class="card">
            <h3>💪 Strength</h3>
            <p>Functional fitness and injury prevention sessions.</p>
        </div>
    </div>

    <a class="cta" href="mailto:join@belgiumcross.team">
        JOIN THE TEAM TODAY
    </a>
</div>

<div class="section">
    <h2>Why Join?</h2>
    <p>
        ✔ Structured training programs  
        ✔ Supportive community  
        ✔ Events & competitions  
        ✔ All levels welcome  
    </p>
</div>

<footer>
    Belgium Cross Team • Train Hard • Stay Humble • Never Quit
</footer>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return html_page


@app.post("/token", response_model=Token, summary="Login and obtain access token")
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: CrossRepository = Depends(get_cross_repository)
):
    """
    OAuth2 compatible token login endpoint.

    Returns a JWT access token for authenticated users.
    """
    username = await authenticate_user(form_data.username, form_data.password, repo)

    if not username:
        auth_logger.warning(f"Invalid login attempt for user: {form_data.username}")
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


@app.get("/crosses", response_model=List[CrossResponse], summary="Get all crosses")
async def get_crosses(
    auth: dict = Depends(require_roles(ALLOWED_ROLES)),
    repo: CrossRepository = Depends(get_cross_repository)
):
    """Retrieve all crosses from the database. Requires PTI, ADMIN, or APTI role."""
    try:
        crosses = await repo.get_all_crosses()
        if not crosses:
            logger.info("No crosses found in database")
        return crosses
    except SQLAlchemyError as e:
        logger.error("Database error fetching crosses: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve crosses"
        )


@app.post("/crosses/{cross_id}", status_code=status.HTTP_201_CREATED, summary="Save multiple runner recordings for a cross")
async def save_cross_recordings(
    cross_id: Annotated[int, Path(gt=-1, description="Cross ID must be a positive integer")],
    recordings: List[RunnerCreate],
    auth: dict = Depends(require_roles(ALLOWED_ROLES)),
    repo: CrossRepository = Depends(get_cross_repository)
):
    """Save multiple runner recordings with times for a specific cross. Requires PTI, ADMIN, or APTI role."""

    if not recordings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recordings list cannot be empty"
        )

    logger.info("Received POST request to /crosses/%s", cross_id)
    logger.info("Number of recordings: %s", len(recordings))

    try:
        runners: List[Runner] = []
        for idx, recording in enumerate(recordings):

            if recording.running_time is None or recording.running_time < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Recording at index {idx}: Running time must be a non-negative number"
                )
            runners.append(Runner(
                running_time=recording.running_time,
                serial_number=None
            ))

        result = await repo.save_recordings(cross_id, runners)
        logger.info("Successfully saved %s recordings for cross %s", len(runners), cross_id)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        logger.error("Database error saving recordings for cross %s: %s", cross_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save cross recordings"
        )


if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    from src.core.ssl_validator import validate_ssl_certificates

    # Get the project root directory (parent of src/)
    project_root = Path(__file__).parent.parent.absolute()

    # SSL certificate paths (handle both running from project root and from src/)
    cert_path = project_root / "src" / "certs" / "cert.pem"
    key_path = project_root / "src" / "certs" / "key.pem"

    logger.info("Looking for certificates at: %s", cert_path)

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