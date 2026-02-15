"""Authentication and authorization utilities for FastAPI."""
import logging
from typing import List, Optional
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader

from src.core.config_reader import get_config
from src.core.oauth2 import get_current_user

# API Key Security
config = get_config()
API_KEY = config.api.secret_key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
auth_logger = logging.getLogger("auth")

# Role assigned to API key authenticated requests
API_KEY_ROLE = "ADMIN"


def _mask_key(key: Optional[str]) -> str:
    """Mask an API key for safe logging, showing only the last 4 characters."""
    if not key:
        return "<empty>"
    if len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for authentication."""
    if api_key != API_KEY:
        auth_logger.warning("Invalid API key attempted: %s", _mask_key(api_key))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return api_key


async def get_current_user_or_api_key(
    api_key: Optional[str] = Security(api_key_header),
    user: dict = Depends(get_current_user)
):
    """
    Combined authentication: accepts either API Key or OAuth2 token.

    If the X-API-Key header is present, it MUST be valid — no silent fallback
    to OAuth2 on a bad key. If the header is absent, OAuth2 token is used.
    """
    if api_key is not None:
        if api_key == API_KEY:
            return {"type": "api_key", "role": API_KEY_ROLE}
        # API key header was provided but is wrong — reject immediately
        auth_logger.warning("Invalid API key attempted: %s", _mask_key(api_key))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    # No API key header — use OAuth2 token
    return {"type": "oauth2", **user}


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control.

    Users (including API key auth) must have an allowed role to access the endpoint.

    :param allowed_roles: List of allowed role names (e.g., ["PTI", "ADMIN", "APTI"])
    :return: Dependency function that verifies user role
    """
    async def role_checker(auth: dict = Depends(get_current_user_or_api_key)):
        # Check if user is active (API key users are always considered active)
        if auth.get("type") != "api_key" and not auth.get("is_active", False):
            auth_logger.warning("User account is inactive")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Check role — applies to BOTH OAuth2 users and API key
        user_role = auth.get("role")
        if user_role not in allowed_roles:
            auth_logger.warning("Role %s not in allowed roles %s", user_role, allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )

        return auth

    return role_checker
