from datetime import datetime

from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10)
    required_skills: str | None = None
    experience_required: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobOut(JobBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    success: bool
    message: str
    data: JobOut | None = None
