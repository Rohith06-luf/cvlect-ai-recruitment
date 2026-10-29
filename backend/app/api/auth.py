"""
CVlect AI — Authentication API Endpoints
Registration, login, profile inspection, and audit logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, AuditEvent
from app.schemas.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new candidate or recruiter account and issue an access token.
    """
    # Check if email is already taken
    existing = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    # Create user
    new_user = User(
        email=user_in.email.lower().strip(),
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name.strip(),
        role=user_in.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Record Audit Event (non-blocking)
    try:
        client_ip = request.client.host if request.client else None
        audit = AuditEvent(
            user_id=new_user.id,
            action="USER_REGISTER",
            resource_type="user",
            resource_id=new_user.id,
            details={"role": new_user.role, "email": new_user.email},
            ip_address=client_ip,
        )
        db.add(audit)
        db.commit()
    except Exception as audit_err:
        logger.warning(f"Audit event recording skipped: {audit_err}")
        db.rollback()

    # Generate token
    token = create_access_token(data={"sub": str(new_user.id), "role": new_user.role})
    logger.info(f"Registered user ID {new_user.id} with role '{new_user.role}'")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials and issue an access token.
    """
    user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently inactive.",
        )

    # Record Audit Event (non-blocking)
    try:
        client_ip = request.client.host if request.client else None
        audit = AuditEvent(
            user_id=user.id,
            action="USER_LOGIN",
            resource_type="user",
            resource_id=user.id,
            details={"role": user.role},
            ip_address=client_ip,
        )
        db.add(audit)
        db.commit()
    except Exception as audit_err:
        logger.warning(f"Audit event recording skipped: {audit_err}")
        db.rollback()

    # Generate token
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    logger.info(f"User ID {user.id} logged in successfully")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve authenticated user profile.
    """
    return UserResponse.model_validate(current_user)
