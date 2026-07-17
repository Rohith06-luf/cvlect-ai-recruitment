from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.schemas.user import UserOut, UserProfileResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserProfileResponse, summary="List users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Recruiter")),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
):
    query = db.query(User)
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    users = query.offset(skip).limit(limit).all()
    return UserProfileResponse(success=True, message="Users fetched", data=None)
