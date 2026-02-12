"""Authentication and authorization utilities for FastAPI."""
from typing import List
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader

from src.core.config_reader import get_config
from src.core.oauth2 import get_current_user

# API Key Security
config = get_config()
API_KEY = config.api.secret_key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for authentication."""
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
