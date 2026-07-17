from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate, JobOut, JobResponse, JobUpdate

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=list[JobOut], summary="List jobs")
async def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
):
    query = db.query(Job)
    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=JobResponse, summary="Create a job")
async def create_job(payload: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("Admin", "Recruiter"))) -> JobResponse:
    job = Job(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobResponse(success=True, message="Job created", data=job)


@router.put("/{job_id}", response_model=JobResponse, summary="Update a job")
async def update_job(job_id: str, payload: JobUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("Admin", "Recruiter"))) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return JobResponse(success=True, message="Job updated", data=job)


@router.delete("/{job_id}", response_model=JobResponse, summary="Delete a job")
async def delete_job(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles("Admin"))) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.delete(job)
    db.commit()
    return JobResponse(success=True, message="Job deleted", data=None)
