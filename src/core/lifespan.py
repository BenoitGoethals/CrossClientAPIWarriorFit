"""Application lifespan management."""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.core.ssl_validator import validate_ssl_certificates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Validates SSL certificates on application startup.
    """
    # Startup: Validate SSL certificates
    cert_path_pem = os.environ.get("SSL_CERTFILE", "./src/certs/cert.pem")
    key_path_pem = os.environ.get("SSL_KEYFILE", "./src/certs/key.pem")

    # Only validate if both files exist (SSL is being used)
    if Path(cert_path_pem).exists() and Path(key_path_pem).exists():
        logger.info("=" * 60)
        logger.info("Validating SSL certificates on startup...")
        validation = validate_ssl_certificates(cert_path_pem, key_path_pem)

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

    yield

    # Shutdown: cleanup code would go here if needed
