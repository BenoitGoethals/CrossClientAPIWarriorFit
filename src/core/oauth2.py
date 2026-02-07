from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.config_reader import get_config

# Argon2 password hasher with secure defaults
# Uses Argon2id (hybrid mode combining Argon2i and Argon2d)
# Resistant to GPU/ASIC attacks due to memory-hardness
ph = PasswordHasher()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Get config
config = get_config()


def verify_password(plain_password: str, hashed_password: str) -> Tuple[bool, bool]:
    """
    Verify a password against its hash (supports both bcrypt and Argon2).

    This function supports migration from bcrypt to Argon2:
    - First tries Argon2 verification (new format)
    - Falls back to bcrypt verification (legacy format)
    - Returns (is_valid, needs_rehash) tuple

    :param plain_password: The plain text password to verify
    :param hashed_password: The stored hash (bcrypt or Argon2 format)
    :return: Tuple of (is_valid, needs_rehash)
        - is_valid: True if password matches
        - needs_rehash: True if hash is bcrypt and should be upgraded to Argon2
    """
    # Try Argon2 first (new format starts with $argon2)
    if hashed_password.startswith('$argon2'):
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
    if hashed_password.startswith(('$2b$', '$2a$', '$2y$')):
        try:
            is_valid = bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
            # If bcrypt password is valid, it needs rehashing to Argon2
            return is_valid, is_valid
        except Exception:
            return False, False

    # Unknown hash format
    return False, False


def get_password_hash(password: str) -> str:
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
    """
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.api.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.api.oauth2_secret_key, algorithm=config.api.algorithm)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> str:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, config.api.oauth2_secret_key, algorithms=[config.api.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


async def authenticate_user(username: str, password: str) -> Optional[str]:
    """
    Authenticate a user using username and password.

    Uses the repository's get_user_credentials method to retrieve the user
    and verifies the password against the stored hash.

    Automatically upgrades bcrypt passwords to Argon2 on successful login.

    :param username: The username to authenticate.
    :param password: The plain-text password to verify.
    :return: The username if authentication succeeds, None otherwise.
    """
    from src.repo.cross_repository import CrossRepository

    repo = CrossRepository()
    user = await repo.get_user_credentials(username)

    if user is None:
        return None

    is_valid, needs_rehash = verify_password(password, user.password_hash)

    if not is_valid:
        return None

    # Automatically upgrade bcrypt passwords to Argon2
    if needs_rehash:
        new_hash = get_password_hash(password)
        await repo.update_password_hash(username, new_hash)

    return user.username


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get the current authenticated user from the token.

    Returns a dict with username and role information.
    """
    from src.repo.cross_repository import CrossRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)

    # Fetch user to get role
    repo = CrossRepository()
    user = await repo.get_user_credentials(username)

    if user is None:
        raise credentials_exception

    return {
        "username": username,
        "role": user.role.value,
        "is_active": user.is_active
    }
