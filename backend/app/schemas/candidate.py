from datetime import datetime

from pydantic import BaseModel, Field


class CandidateBase(BaseModel):
    phone: str | None = None
    experience: str | None = None
    education: str | None = None
    skills: str | None = None
    location: str | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(CandidateBase):
    pass


class CandidateOut(CandidateBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateResponse(BaseModel):
    success: bool
    message: str
    data: CandidateOut | None = None
