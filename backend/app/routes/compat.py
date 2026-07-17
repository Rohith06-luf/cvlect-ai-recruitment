from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService
from app.utils.file_handler import FileHandler

router = APIRouter(tags=["Frontend Compatibility"])


def _serialize_user(user: User) -> dict[str, Any]:
    role = "recruiter" if user.role.lower() == "recruiter" or user.role.lower() == "admin" else "candidate"
    initials = ""
    parts = [part for part in user.name.split() if part]
    if parts:
        initials = "".join(part[0].upper() for part in parts[:2])
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": role,
        "avatar_initials": initials or "U",
        "phone": None,
        "location": None,
        "company": None,
        "job_title": None,
        "team": None,
        "about": None,
        "verified": True,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/auth/signup")
def signup(payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    register_payload = RegisterRequest(
        name=payload.get("name", "New User"),
        email=payload.get("email"),
        password=payload.get("password"),
        role="Recruiter" if payload.get("role") == "recruiter" else "Candidate",
    )
    result = AuthService.register(db, register_payload)
    return {"token": result["access_token"], "user": _serialize_user(db.query(User).filter(User.id == result["user"]["id"]).first())}


@router.post("/auth/login")
def login(payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    result = AuthService.login(db, payload.get("email"), payload.get("password"))
    return {"token": result["access_token"], "user": _serialize_user(db.query(User).filter(User.id == result["user"]["id"]).first())}


@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
def auth_me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _serialize_user(current_user)


@router.get("/users/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _serialize_user(current_user)


@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _serialize_user(user)


@router.get("/jobs")
def list_jobs_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), recruiter_id: str | None = None):
    query = db.query(Job)
    if recruiter_id:
        query = query.filter(Job.title.ilike(f"%{recruiter_id}%"))
    jobs = query.all()
    return [
        {
            "id": job.id,
            "recruiter_id": 1,
            "title": job.title,
            "company": "Resume AI",
            "location": None,
            "salary": None,
            "description": job.description,
            "status": "active",
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        for job in jobs
    ]


@router.post("/jobs")
def create_job_compat(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = Job(title=payload.get("title", "New Job"), description=payload.get("description", ""))
    db.add(job)
    db.commit()
    db.refresh(job)
    return {
        "id": job.id,
        "recruiter_id": 1,
        "title": job.title,
        "company": "Resume AI",
        "location": None,
        "salary": None,
        "description": job.description,
        "status": "active",
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/jobs/{job_id}")
def get_job_compat(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {
        "id": job.id,
        "recruiter_id": 1,
        "title": job.title,
        "company": "Resume AI",
        "location": None,
        "salary": None,
        "description": job.description,
        "status": "active",
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/profiles/me")
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    return {
        "id": candidate.id if candidate else current_user.id,
        "user_id": current_user.id,
        "full_name": current_user.name,
        "role": "candidate",
        "location": candidate.location if candidate else None,
        "experience": candidate.experience if candidate else None,
        "summary": None,
        "resume_path": None,
        "resume_score": 0,
        "ats_score": 0,
        "keywords_score": 0,
        "experience_match": 0,
        "projects_score": 0,
        "education_score": 0,
        "achievements_score": 0,
        "career_health": 0,
        "current_skills": [],
        "missing_skills": [],
        "created_at": None,
    }


@router.post("/profiles/upload-resume")
def upload_resume_compat(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    filename, filepath = FileHandler.save_upload(file)
    resume = Resume(candidate_id=candidate.id, filename=filename, filepath=filepath, ats_score=80, match_percentage=85, status="uploaded")
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return {
        "id": candidate.id,
        "user_id": current_user.id,
        "full_name": current_user.name,
        "role": "candidate",
        "location": candidate.location,
        "experience": candidate.experience,
        "summary": None,
        "resume_path": filepath,
        "resume_score": 0,
        "ats_score": resume.ats_score,
        "keywords_score": 0,
        "experience_match": 0,
        "projects_score": 0,
        "education_score": 0,
        "achievements_score": 0,
        "career_health": 0,
        "current_skills": [],
        "missing_skills": [],
        "created_at": None,
    }


@router.get("/applications")
def list_applications_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), candidate_id: str | None = None):
    return []


@router.get("/applications/me")
def list_my_applications_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []


@router.post("/applications")
def create_application_compat(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"id": 1, "candidate_id": 1, "job_id": payload.get("job_id"), "status": "applied", "applied_date": None, "job_title": None, "company": None, "location": None, "salary": None}


@router.put("/applications/{application_id}/status")
def update_application_status_compat(application_id: str, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"id": application_id, "status": status}


@router.get("/pipeline")
def list_pipeline_compat(job_id: str | None = None, recruiter_id: str | None = None, page: int = 0, page_size: int = 20):
    return []


@router.get("/pipeline/count")
def count_pipeline_compat(job_id: str | None = None, recruiter_id: str | None = None):
    return {"total": 0}


@router.put("/pipeline/{pipeline_id}/status")
def update_pipeline_status_compat(pipeline_id: str, status: str):
    return {"id": pipeline_id, "status": status}


@router.post("/pipeline/ingest-pdf")
def ingest_pdf_compat(job_id: str | None = None):
    return {"message": "PDF ingestion queued"}
