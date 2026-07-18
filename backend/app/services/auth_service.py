from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_password_hash, create_refresh_token, verify_password
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.auth import RegisterRequest


class AuthService:
    @staticmethod
    def register(db: Session, payload: RegisterRequest) -> dict[str, Any]:
        existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(
            name=payload.name.strip(),
            email=payload.email.lower(),
            hashed_password=create_password_hash(payload.password),
            role=payload.role.strip().title(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        if payload.role.strip().lower() == "candidate":
            candidate = Candidate(
                user_id=user.id,
                phone=payload.phone,
                location=payload.location,
                experience=payload.experience,
                education=payload.education,
                skills=payload.skills,
            )
            db.add(candidate)
            db.commit()

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
            },
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": create_refresh_token(user.id),
        }

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict[str, Any]:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
            },
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": create_refresh_token(user.id),
        }

    @staticmethod
    def refresh(db: Session, refresh_token: str) -> dict[str, Any]:
        from app.core.security import decode_token

        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        return {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": create_refresh_token(user.id),
        }
