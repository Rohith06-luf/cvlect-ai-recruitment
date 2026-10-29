"""
CVlect AI — Applications API Endpoints
Job application submission, role-based application pipeline viewing, and status updates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Application, Job, Resume, User
from app.schemas.schemas import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationResponse,
)
from app.services.auth_service import get_current_user, require_candidate
from app.services.matching_engine import analyze_match
from app.utils import get_logger, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/applications", tags=["Applications"])


def _format_application_response(app: Application) -> ApplicationResponse:
    """Helper to convert ORM model to rich ApplicationResponse schema."""
    return ApplicationResponse(
        id=app.id,
        candidate_id=app.candidate_id,
        job_id=app.job_id,
        resume_id=app.resume_id,
        status=app.status,
        cover_letter=app.cover_letter,
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        job_title=app.job.title if app.job else None,
        company=app.job.company if app.job else None,
        candidate_name=app.candidate.full_name if app.candidate else None,
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def submit_application(
    app_in: ApplicationCreate,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """
    Submit an application to an active job opening.
    """
    # Verify Job
    job = db.query(Job).filter(Job.id == app_in.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opening not found.")
    if job.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply to a job that is no longer active.",
        )

    # Verify Resume
    resume = (
        db.query(Resume)
        .filter(Resume.id == app_in.resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified resume not found or does not belong to you.",
        )

    # Check for Duplicate Application
    existing = (
        db.query(Application)
        .filter(Application.candidate_id == current_user.id, Application.job_id == app_in.job_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted an application for this position.",
        )

    # Automatically compute match result if not yet calculated
    if resume.extracted_data:
        try:
            analyze_match(resume_data=resume.extracted_data, job=job, db=db)
        except Exception as e:
            logger.warning(f"Could not compute initial match score on application: {e}")

    application = Application(
        candidate_id=current_user.id,
        job_id=job.id,
        resume_id=resume.id,
        status="applied",
        cover_letter=app_in.cover_letter,
        applied_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    logger.info(f"Candidate {current_user.id} applied to Job {job.id}")
    return _format_application_response(application)


@router.get("", response_model=list[ApplicationResponse])
@router.get("/", response_model=list[ApplicationResponse], include_in_schema=False)
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List applications based on role:
      - Candidates see all applications they submitted.
      - Recruiters see all applications submitted to jobs they posted.
    """
    if current_user.role == "candidate":
        apps = (
            db.query(Application)
            .filter(Application.candidate_id == current_user.id)
            .order_by(Application.applied_at.desc())
            .all()
        )
    else:
        # Recruiter
        apps = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(Job.recruiter_id == current_user.id)
            .order_by(Application.applied_at.desc())
            .all()
        )

    return [_format_application_response(a) for a in apps]


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update application status:
      - Recruiters can advance candidate pipeline statuses (reviewing, shortlisted, interview, offered, rejected).
      - Candidates can only withdraw their application.
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    new_status = status_update.status.lower()

    if current_user.role == "candidate":
        if application.candidate_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        if new_status != "withdrawn":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidates may only withdraw their application.",
            )
    elif current_user.role == "recruiter":
        if not application.job or application.job.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update applications for jobs you posted.",
            )

    application.status = new_status
    application.updated_at = utcnow()
    db.commit()
    db.refresh(application)

    logger.info(f"Application {application.id} status updated to '{new_status}' by User {current_user.id}")
    return _format_application_response(application)
