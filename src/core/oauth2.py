import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.config_reader import get_config
from src.core.dependencies import get_cross_repository
from src.data.repo.cross_repository import CrossRepository

# Argon2 password hasher with secure defaults
# Uses Argon2id (hybrid mode combining Argon2i and Argon2d)
# Resistant to GPU/ASIC attacks due to memory-hardness
ph = PasswordHasher()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Get config
config = get_config()
auth_logger = logging.getLogger("auth")


def _verify_password_sync(plain_password: str, hashed_password: str) -> Tuple[bool, bool]:
    """
    Synchronous password verification (internal use only).

    This is the blocking implementation that will be run in a thread pool.
    """
    # Try Argon2 first (new format starts with $argon2)
    if hashed_password.startswith("$argon2"):
        try:
            ph.verify(hashed_password, plain_password)
            # Check if parameters need upgrade
            needs_rehash = ph.check_needs_rehash(hashed_password)
            return True, needs_rehash
        except VerifyMismatchError:
            return False, False
        except (InvalidHashError, Exception):
            return False, False

    # Fall back to bcrypt (legacy format starts with $2b$, $2a$, or $2y$)
    if hashed_password.startswith(("$2b$", "$2a$", "$2y$")):
        try:
            is_valid = bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
            # If bcrypt password is valid, it needs rehashing to Argon2
            return is_valid, is_valid
        except Exception:
            return False, False

    # Unknown hash format
    return False, False


async def verify_password(plain_password: str, hashed_password: str) -> Tuple[bool, bool]:
    """
    Verify a password against its hash (supports both bcrypt and Argon2).

    This function supports migration from bcrypt to Argon2:
    - First tries Argon2 verification (new format)
    - Falls back to bcrypt verification (legacy format)
    - Returns (is_valid, needs_rehash) tuple

    Runs in a thread pool to avoid blocking the event loop.

    :param plain_password: The plain text password to verify
    :param hashed_password: The stored hash (bcrypt or Argon2 format)
    :return: Tuple of (is_valid, needs_rehash)
        - is_valid: True if password matches
        - needs_rehash: True if hash is bcrypt and should be upgraded to Argon2
    """
    return await asyncio.to_thread(_verify_password_sync, plain_password, hashed_password)


def _get_password_hash_sync(password: str) -> str:
    """
    Synchronous password hashing (internal use only).

    This is the blocking implementation that will be run in a thread pool.
    """
    return ph.hash(password)


async def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2id.

    Argon2id is the winner of the Password Hashing Competition (2015) and provides:
    - Memory-hard algorithm (resistant to GPU/ASIC attacks)
    - Side-channel resistance
    - Configurable time and memory costs
    - Built-in salt generation
    - Stronger security than bcrypt, scrypt, and PBKDF2

    Default parameters (from argon2-cffi):
    - time_cost: 2 iterations
    - memory_cost: 102400 KiB (100 MiB)
    - parallelism: 8 threads
    - hash_len: 16 bytes
    - salt_len: 16 bytes

    Runs in a thread pool to avoid blocking the event loop.
    """
    return await asyncio.to_thread(_get_password_hash_sync, password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=config.api.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.api.oauth2_secret_key, algorithm=config.api.algorithm
    )
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> str:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, config.api.oauth2_secret_key, algorithms=[config.api.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


async def authenticate_user(
    username: str, password: str, repo: CrossRepository
) -> Optional[str]:
    """
    Authenticate a user using username and password.

    Uses the repository's get_user_credentials method to retrieve the user
    and verifies the password against the stored hash.

    Automatically upgrades bcrypt passwords to Argon2 on successful login.

    :param username: The username to authenticate.
    :param password: The plain-text password to verify.
    :param repo: The repository used to fetch user credentials.
    :return: The username if authentication succeeds, None otherwise.
    """
    user = await repo.get_user_credentials(username)

    if user is None:
        return None

    is_valid, needs_rehash = await verify_password(password, user.password_hash)

    if not is_valid:
        auth_logger.warning("Invalid password for user: %s", username)
        return None

    # Automatically upgrade bcrypt passwords to Argon2
    if needs_rehash:
        new_hash = await get_password_hash(password)
        await repo.update_password_hash(username, new_hash)

    return user.username


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: CrossRepository = Depends(get_cross_repository),
) -> dict:
    """
    Get the current authenticated user from the token.

    Returns a dict with username and role information.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)

    # Fetch user to get role
    user = await repo.get_user_credentials(username)

    if user is None:
        auth_logger.warning(f"Invalid token for user: {username}")
        raise credentials_exception

    return {"username": username, "role": user.role.value, "is_active": user.is_active}
