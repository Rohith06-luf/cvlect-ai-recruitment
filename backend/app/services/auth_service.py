"""
CVlect AI — Authentication & Authorization Service
Handles password hashing, JWT generation and verification, and role-based FastAPI dependencies.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
from jose import jwt, JWTError
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        """Hash a plaintext password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False
except ImportError:
    import hashlib
    import secrets

    def hash_password(password: str) -> str:
        """Hash a plaintext password using pbkdf2_hmac fallback."""
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"pbkdf2:sha256:100000${salt}${key.hex()}"

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against pbkdf2 hash."""
        try:
            if hashed_password.startswith("pbkdf2:sha256:"):
                parts = hashed_password.split("$")
                salt = parts[1]
                key = parts[2]
                computed = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
                return secrets.compare_digest(computed.hex(), key)
            return False
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import User
from app.utils import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.
    'sub' claim should typically store user_id as a string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode failed: {e}")
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to extract and validate the authenticated user from the Bearer token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if not payload:
        raise credentials_exception

    user_id_raw = payload.get("sub") or payload.get("user_id")
    if user_id_raw is None:
        raise credentials_exception

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(required_role: str) -> Callable[[User], User]:
    """
    Factory creating a FastAPI dependency that verifies the user has the required role.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires '{required_role}' role",
            )
        return current_user

    return role_checker


# Pre-defined dependencies for candidate and recruiter roles
require_candidate = require_role("candidate")
require_recruiter = require_role("recruiter")
