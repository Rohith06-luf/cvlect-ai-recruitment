"""
CVlect AI — Jobs API Endpoints
Creation, listing, searching, pagination, updates, and deletion of job postings.
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.models import Job, User
from app.schemas.schemas import JobCreate, JobUpdate, JobResponse, PaginatedJobsResponse
from app.services.auth_service import require_recruiter, get_current_user
from app.services.nlp_engine import extract_job_requirements
from app.services.embedding_service import generate_embedding, embedding_to_bytes
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_job(
    job_in: JobCreate,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """
    Create a new job posting (recruiters only).
    Automatically extracts structured requirements from the job description if not explicitly passed,
    and generates dense vector embeddings.
    """
    # NLP extraction fallback if fields omitted
    nlp_extracted = extract_job_requirements(job_in.description)

    required_skills = job_in.required_skills if job_in.required_skills is not None else nlp_extracted.get("required_skills", [])
    preferred_skills = job_in.preferred_skills if job_in.preferred_skills is not None else nlp_extracted.get("preferred_skills", [])
    education_reqs = job_in.education_requirements if job_in.education_requirements is not None else nlp_extracted.get("education", [])
    certifications = job_in.certifications if job_in.certifications is not None else nlp_extracted.get("certifications", [])
    responsibilities = job_in.responsibilities if job_in.responsibilities is not None else nlp_extracted.get("responsibilities", [])
    technologies = job_in.technologies if job_in.technologies is not None else nlp_extracted.get("technologies", [])
    seniority = job_in.seniority or nlp_extracted.get("seniority", "mid")
    category = job_in.category or nlp_extracted.get("category", "Software Engineering")

    # Generate dense semantic vector
    embed_text = f"{job_in.title} {job_in.company} {job_in.description}"[:2500]
    embedding_arr = generate_embedding(embed_text)
    emb_bytes = embedding_to_bytes(embedding_arr)

    job = Job(
        recruiter_id=current_user.id,
        title=job_in.title.strip(),
        company=job_in.company.strip(),
        description=job_in.description.strip(),
        location=job_in.location.strip() if job_in.location else None,
        work_mode=job_in.work_mode,
        experience_min=job_in.experience_min,
        experience_max=job_in.experience_max,
        salary_min=job_in.salary_min,
        salary_max=job_in.salary_max,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        education_requirements=education_reqs,
        certifications=certifications,
        responsibilities=responsibilities,
        technologies=technologies,
        seniority=seniority,
        category=category,
        status=job_in.status,
        embedding=emb_bytes,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Job created: '{job.title}' by recruiter {current_user.id}")
    return JobResponse.model_validate(job)


@router.get("", response_model=PaginatedJobsResponse)
@router.get("/", response_model=PaginatedJobsResponse, include_in_schema=False)
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status (active, closed, draft)"),
    location: Optional[str] = Query(None, description="Filter by location substring"),
    work_mode: Optional[str] = Query(None, description="Filter by remote/onsite/hybrid"),
    category: Optional[str] = Query(None, description="Filter by industry category"),
    search: Optional[str] = Query(None, description="Search across title, company, description"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter job listings with pagination.
    """
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    else:
        # Default to active jobs for general listing
        query = query.filter(Job.status == "active")

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if work_mode:
        query = query.filter(Job.work_mode == work_mode)

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
                Job.description.ilike(search_pattern),
            )
        )

    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 1

    jobs = (
        query.order_by(Job.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedJobsResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve full details of a specific job posting.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found.",
        )
    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_update: JobUpdate,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """
    Update a job posting. Only the owning recruiter can edit their job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found.",
        )

    if job.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update job postings that you created.",
        )

    update_data = job_update.model_dump(exclude_unset=True)

    text_changed = False
    for field, value in update_data.items():
        if field in ["title", "description", "company"]:
            text_changed = True
        setattr(job, field, value)

    # Regenerate dense embedding if text changed
    if text_changed:
        embed_text = f"{job.title} {job.company} {job.description}"[:2500]
        embedding_arr = generate_embedding(embed_text)
        job.embedding = embedding_to_bytes(embedding_arr)

    db.commit()
    db.refresh(job)

    logger.info(f"Job {job.id} updated by recruiter {current_user.id}")
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """
    Delete a job posting. Only the owning recruiter can delete their job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found.",
        )

    if job.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete job postings that you created.",
        )

    db.delete(job)
    db.commit()

    logger.info(f"Job {job_id} deleted by recruiter {current_user.id}")
    return None
