from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, summary="Register a new user")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        result = AuthService.register(db, payload)
    except HTTPException as exc:
        raise exc

    return AuthResponse(success=True, message="Registration successful", data={"user": result["user"], "access_token": result["access_token"], "refresh_token": result["refresh_token"]})


@router.post("/login", response_model=AuthResponse, summary="Login with email and password")
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        result = AuthService.login(db, payload.email, payload.password)
    except HTTPException as exc:
        raise exc

    return AuthResponse(success=True, message="Login successful", data={"user": result["user"], "access_token": result["access_token"], "refresh_token": result["refresh_token"]})


@router.post("/refresh", response_model=AuthResponse, summary="Refresh access token")
async def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AuthResponse:
    result = AuthService.refresh(db, payload.refresh_token)
    return AuthResponse(success=True, message="Token refreshed", data={"access_token": result["access_token"], "refresh_token": result["refresh_token"]})


@router.post("/logout", response_model=AuthResponse, summary="Logout user")
async def logout(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(success=True, message="Logout successful", data={})


@router.get("/me", response_model=AuthResponse, summary="Get current user details")
async def get_me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(success=True, message="Current user fetched", data={"user": {"id": current_user.id, "name": current_user.name, "email": current_user.email, "role": current_user.role, "created_at": current_user.created_at}})
