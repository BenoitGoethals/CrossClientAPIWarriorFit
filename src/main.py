"""WarriorFit API - FastAPI application for running event management."""
import logging
from typing import List, Annotated
from datetime import timedelta
from starlette.responses import RedirectResponse
from src.data.model.db_model import Runner
from src.data.model.schemas import CrossResponse, RunnerResponse, RunnerCreate, Token
from src.data.repo.cross_repository import CrossRepository
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

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuration
config = get_config()

# FastAPI application
app = FastAPI(
    title="WarriorFit API",
    description="API for accessing the WarriorFit running event database",
    version=load_version(),
    docs_url="/docs",
    port=8550,
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

# Repository
repo = CrossRepository()

# Define allowed roles for API access
ALLOWED_ROLES = ["PTI", "ADMIN", "APTI"]


@app.get("/", summary="Redirect to API documentation")
async def root():
    """Redirect to the interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.post("/token", response_model=Token, summary="Login and obtain access token")
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


@app.get("/crosses", response_model=List[CrossResponse], summary="Get all crosses")
async def get_crosses(auth: dict = Depends(require_roles(ALLOWED_ROLES))):
    """Retrieve all crosses from the database. Requires PTI, ADMIN, or APTI role."""
    try:
        crosses = await repo.get_all_crosses()
        if not crosses:
            logger.info("No crosses found in database")
        return crosses
    except Exception as e:
        logger.error(f"Error fetching crosses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve crosses"
        )

@app.get("/crosses/{id_cross}", response_model=CrossResponse, summary="Get cross by ID")
async def get_cross(
    id_cross: Annotated[int, Path(gt=0, description="Cross ID must be a positive integer")],
    auth: dict = Depends(require_roles(ALLOWED_ROLES))
):
    """Retrieve a specific cross by its unique identifier. Requires PTI, ADMIN, or APTI role."""
    try:
        cross = await repo.get_cross(id_cross)
        if not cross:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cross with ID {id_cross} not found"
            )
        return cross
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cross {id_cross}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cross"
        )

@app.post("/crosses/{serial_number}/{id_cross}", status_code=status.HTTP_201_CREATED, summary="Add runner to cross by serial number")
async def add_runner(
    serial_number: Annotated[str, Path(min_length=1, description="Runner serial number")],
    id_cross: Annotated[int, Path(gt=0, description="Cross ID must be a positive integer")],
    auth: dict = Depends(require_roles(ALLOWED_ROLES))
):
    """Associate a runner with a cross using the runner's serial number. Requires PTI, ADMIN, or APTI role."""
    if not serial_number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial number cannot be empty"
        )

    try:
        result = await repo.add_runner(serial_number.strip(), id_cross)
        logger.info(f"Runner {serial_number} added to cross {id_cross}")
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding runner {serial_number} to cross {id_cross}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add runner to cross"
        )

@app.get("/crosses/runners/{cross_id}", response_model=List[RunnerResponse], summary="Get all runners for a cross")
async def get_runners(
    cross_id: Annotated[int, Path(gt=0, description="Cross ID must be a positive integer")],
    auth: dict = Depends(require_roles(ALLOWED_ROLES))
):
    """Retrieve all runners associated with a specific cross. Requires PTI, ADMIN, or APTI role."""
    try:
        runners = await repo.get_all_runners(cross_id)
        if not runners:
            logger.info(f"No runners found for cross {cross_id}")
        return runners
    except Exception as e:
        logger.error(f"Error fetching runners for cross {cross_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve runners"
        )

@app.post("/crosses/runner/{serial_number}/{id_cross}", status_code=status.HTTP_201_CREATED, summary="Add runner to cross (alternate endpoint)")
async def add_runner_duplicate(
    serial_number: Annotated[str, Path(min_length=1, description="Runner serial number")],
    id_cross: Annotated[int, Path(gt=0, description="Cross ID must be a positive integer")],
    auth: dict = Depends(require_roles(ALLOWED_ROLES))
):
    """
    Add runner to a cross using an alternate endpoint.

    This function provides functionality to associate a runner with a cross. The runner
    is identified by their serial number, and the cross is identified by its ID. The request
    requires authorization based on specific roles.

    :param serial_number: The serial number of the runner. The serial number cannot be an
        empty string.
    :param id_cross: The unique identifier of the cross. It must be a positive integer.
    :param auth: Dictionary containing authentication information; provided automatically
        via dependency injection.
    :return: A dictionary or object containing the result of the operation, such as
        confirmation of the runner being added to the cross.
    :raises HTTPException: Raised if the serial number is empty, if the operation fails
        due to a bad request, or if an unexpected error occurs during the process.
    """
    if not serial_number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial number cannot be empty"
        )

    try:
        result = await repo.add_runner(serial_number.strip(), id_cross)
        logger.info(f"Runner {serial_number} added to cross {id_cross}")
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding runner {serial_number} to cross {id_cross}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add runner to cross"
        )

@app.post("/crosses/{cross_id}", status_code=status.HTTP_201_CREATED, summary="Save multiple runner recordings for a cross")
async def save_cross_recordings(
    cross_id: Annotated[int, Path(gt=-1, description="Cross ID must be a positive integer")],
    recordings: List[RunnerCreate],
    auth: dict = Depends(require_roles(ALLOWED_ROLES))
):
    """Save multiple runner recordings with times for a specific cross. Requires PTI, ADMIN, or APTI role."""

    if not recordings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recordings list cannot be empty"
        )

    logger.info(f"Received POST request to /crosses/{cross_id}")
    logger.info(f"Number of recordings: {len(recordings)}")

    try:
        runners: List[Runner] = []
        for idx, recording in enumerate(recordings):
            if not recording.serial_number or not recording.serial_number.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Recording at index {idx}: Serial number cannot be empty"
                )
            if recording.running_time is None or recording.running_time < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Recording at index {idx}: Running time must be a non-negative number"
                )
            runners.append(Runner(
                running_time=recording.running_time,
                serial_number=recording.serial_number.strip()
            ))

        result = await repo.save_recordings(cross_id, runners)
        logger.info(f"Successfully saved {len(runners)} recordings for cross {cross_id}")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error saving recordings for cross {cross_id}: {str(e)}", exc_info=True)
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