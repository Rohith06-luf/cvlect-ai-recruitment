"""
CVlect AI — Saved Jobs API Endpoints
Bookmark and manage saved job openings for candidates.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import SavedJob, Job, User
from app.schemas.schemas import SavedJobResponse
from app.services.auth_service import require_candidate
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/saved-jobs", tags=["Saved Jobs"])


@router.get("", response_model=List[SavedJobResponse])
@router.get("/", response_model=List[SavedJobResponse], include_in_schema=False)
def list_saved_jobs(
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """List all saved jobs for current candidate."""
    saved = (
        db.query(SavedJob)
        .filter(SavedJob.candidate_id == current_user.id)
        .order_by(SavedJob.saved_at.desc())
        .all()
    )
    return saved


@router.post("/{job_id}")
def save_job(
    job_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """Save/bookmark a job listing."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job opening not found.",
        )

    existing = (
        db.query(SavedJob)
        .filter(SavedJob.candidate_id == current_user.id, SavedJob.job_id == job_id)
        .first()
    )
    if not existing:
        new_saved = SavedJob(candidate_id=current_user.id, job_id=job_id)
        db.add(new_saved)
        db.commit()

    return {"message": "Job successfully saved.", "saved": True}


@router.delete("/{job_id}")
def unsave_job(
    job_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """Remove a job from saved bookmarks."""
    existing = (
        db.query(SavedJob)
        .filter(SavedJob.candidate_id == current_user.id, SavedJob.job_id == job_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()

    return {"message": "Job removed from saved listings.", "saved": False}
