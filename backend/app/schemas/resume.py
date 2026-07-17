from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: str
    candidate_id: str
    filename: str
    filepath: str
    ats_score: int | None = None
    match_percentage: int | None = None
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ResumeResponse(BaseModel):
    success: bool
    message: str
    data: ResumeOut | None = None
    ai_analysis: dict[str, Any] | None = None
