from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.ai_service import AIService
from app.services.auth_service import AuthService
from app.utils.file_handler import FileHandler

router = APIRouter(tags=["Frontend Compatibility"])


def _build_profile_update_payload(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    user_data: dict[str, Any] = {}
    candidate_data: dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"name", "phone", "company", "job_title", "team", "about"}:
            user_data[key] = value
        elif key in {"location", "experience", "education", "skills", "summary"}:
            candidate_data[key] = value
    return {"user_data": user_data, "candidate_data": candidate_data}


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
        phone=payload.get("phone"),
        location=payload.get("location"),
        company=payload.get("company"),
        job_title=payload.get("job_title"),
        team=payload.get("team"),
        about=payload.get("about"),
        experience=payload.get("experience"),
        education=payload.get("education"),
        skills=payload.get("skills"),
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


import json
from uuid import uuid4

@router.get("/resumes/folder")
def list_resume_folder(current_user: User = Depends(get_current_user)) -> list[dict[str, str]]:
    root = Path(__file__).resolve().parents[3] / "Resume"
    if not root.exists():
        return []
    files = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in {".pdf", ".doc", ".docx"}:
            files.append({"name": path.name, "path": str(path)})
    return files


@router.get("/profiles/me")
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        return {
            "id": current_user.id,
            "user_id": current_user.id,
            "full_name": current_user.name,
            "role": "candidate",
            "location": None,
            "experience": None,
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

    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.uploaded_at.desc()).first()

    skills = []
    if resume and resume.skills_list:
        try:
            skills = json.loads(resume.skills_list)
        except Exception:
            skills = resume.skills_list.split(",")

    latest_app = db.query(Application).filter(Application.candidate_id == candidate.id).order_by(Application.created_at.desc()).first()

    return {
        "id": candidate.id,
        "user_id": current_user.id,
        "full_name": current_user.name,
        "role": "candidate",
        "location": candidate.location or current_user.location,
        "experience": candidate.experience,
        "summary": candidate.summary or (resume.summary if resume else None),
        "resume_path": resume.filepath if resume else None,
        "resume_score": latest_app.score if latest_app else (resume.match_percentage if resume else 0),
        "ats_score": resume.ats_score if resume else 0,
        "keywords_score": int(latest_app.semantic_similarity * 100) if latest_app else (int(resume.ats_score * 0.8) if resume else 0),
        "experience_match": int(latest_app.score * 0.9) if latest_app else 70,
        "projects_score": int((resume.fraud_score or 0.1) * 100) if resume else 0,
        "education_score": int(resume.ats_score * 0.9) if resume else 0,
        "achievements_score": 85,
        "career_health": resume.match_percentage if resume else 0,
        "current_skills": skills,
        "missing_skills": json.loads(latest_app.missing_skills) if latest_app and latest_app.missing_skills else [],
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }


@router.put("/profiles/me")
def update_my_profile(payload: dict[str, Any], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    update_payload = _build_profile_update_payload(payload)
    user_data = update_payload["user_data"]
    candidate_data = update_payload["candidate_data"]

    if user_data:
        for key, value in user_data.items():
            if hasattr(current_user, key):
                setattr(current_user, key, value)
        db.add(current_user)

    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    for key, value in candidate_data.items():
        setattr(candidate, key, value)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    db.refresh(current_user)
    return get_my_profile(current_user=current_user, db=db)


@router.post("/profiles/upload-resume")
def upload_resume_compat(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    filename, filepath = FileHandler.save_upload(file)
    ai_service = AIService()
    ai_result = ai_service.process_resume(filepath)
    
    parsed = ai_result.get("parsed", {})
    features = ai_result.get("features", {})
    fraud = ai_result.get("fraud_report", {})
    bias = ai_result.get("bias_report", {})
    summary = ai_result.get("summary", {})

    resume = Resume(
        candidate_id=candidate.id,
        filename=filename,
        filepath=filepath,
        ats_score=ai_result["ats_score"],
        match_percentage=ai_result["match_percentage"],
        status="uploaded",
        raw_text=ai_result.get("text"),
        skills_list=json.dumps(parsed.get("skills", [])),
        experience_years=parsed.get("experience_years", 0),
        parsed_education=json.dumps(parsed.get("education", [])),
        parsed_projects=json.dumps(parsed.get("projects", [])),
        parsed_certifications=json.dumps(parsed.get("certifications", [])),
        summary=summary.get("summary"),
        fraud_score=fraud.get("risk_score"),
        fraud_warnings=json.dumps(fraud.get("warnings", [])),
        bias_score=bias.get("bias_score"),
        bias_flagged_terms=json.dumps(bias.get("flagged_terms", []))
    )
    db.add(resume)
    
    # Save parsed experience details back to Candidate table
    candidate.experience = f"{parsed.get('experience_years', 0)} years"
    candidate.skills = ", ".join(parsed.get("skills", []))
    if parsed.get("education"):
        candidate.education = ", ".join(parsed.get("education"))
        
    db.commit()
    db.refresh(resume)
    db.refresh(candidate)

    return {
        "id": candidate.id,
        "user_id": current_user.id,
        "full_name": current_user.name,
        "role": "candidate",
        "location": candidate.location,
        "experience": candidate.experience,
        "summary": resume.summary,
        "resume_path": filepath,
        "resume_score": resume.match_percentage,
        "ats_score": resume.ats_score,
        "keywords_score": int(round(features.get("skill_overlap", 0.0) * 100)),
        "experience_match": int(round(features.get("experience_years", 0) / 10 * 100)),
        "projects_score": int(round(features.get("projects_score", 0.0) * 100)),
        "education_score": int(round(features.get("education_score", 0.0) * 100)),
        "achievements_score": int(round(features.get("certifications_score", 0.0) * 100)),
        "career_health": resume.match_percentage,
        "current_skills": parsed.get("skills", []),
        "missing_skills": [],
        "created_at": None,
        "ai_analysis": {
            "explanation": ai_result.get("explanation"),
            "fraud_report": fraud,
            "bias_report": bias,
        },
    }


@router.get("/applications")
def list_applications_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), candidate_id: str | None = None):
    query = db.query(Application)
    if candidate_id:
        query = query.filter(Application.candidate_id == candidate_id)
    elif current_user.role.lower() == "candidate":
        candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if candidate:
            query = query.filter(Application.candidate_id == candidate.id)
            
    apps = query.all()
    return [
        {
            "id": app.id,
            "candidate_id": app.candidate_id,
            "job_id": app.job_id,
            "status": app.status,
            "applied_date": app.created_at.isoformat() if app.created_at else None,
            "job_title": app.job.title if app.job else "Position",
            "company": "Resume AI",
            "location": "Remote",
            "salary": None
        }
        for app in apps
    ]


@router.post("/ai/recommendations")
def ai_recommendations_compat(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    ai_service = AIService()
    ranked_candidates = payload.get("candidates", [])
    limit = int(payload.get("limit", 5))
    recommendations = ai_service.recommend(ranked_candidates, limit=limit)
    return {"success": True, "data": recommendations}


@router.post("/ai/search")
def ai_search_compat(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    ai_service = AIService()
    query = payload.get("query", "")
    top_k = int(payload.get("limit", 5))
    results = ai_service.search_vector_store(query, top_k=top_k)
    return {"success": True, "data": [{"score": round(score, 4), "candidate": candidate} for score, candidate in results]}


@router.get("/applications/me")
def list_my_applications_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        return []
    return list_applications_compat(db, current_user, candidate_id=candidate.id)


@router.post("/applications")
def create_application_compat(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        candidate = Candidate(user_id=current_user.id)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

    job_id = payload.get("job_id")
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check duplicate
    existing = db.query(Application).filter(Application.candidate_id == candidate.id, Application.job_id == job_id).first()
    if existing:
        return existing

    # Run matching for new application
    resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.uploaded_at.desc()).first()
    
    score = 0
    reason = "No resume uploaded"
    matched_s = []
    missing_s = []
    shap_v = {}
    semantic_sim = 0.0
    recommended_courses = []
    recommended_certs = []

    if resume:
        ai_service = AIService()
        scored_cand = ai_service.score_candidate(resume.raw_text or "", job.description)
        score = scored_cand.get("match_percentage", 0)
        explanation = scored_cand.get("explanation", {})
        reason = scored_cand.get("summary", {}).get("summary", "")
        
        parsed = scored_cand.get("parsed_resume", {})
        skills = {s.lower() for s in parsed.get("skills", [])}
        job_skills = ai_service.recommender._extract_skills_from_text(job.description.lower())
        matched_s = list(skills & job_skills)
        missing_s = list(job_skills - skills)
        shap_v = explanation.get("shap_values", {})
        semantic_sim = float(scored_cand.get("features", {}).get("semantic_similarity", 0.0))
        
        recs = ai_service.recommend([scored_cand], limit=1)[0].get("recommendations", {})
        recommended_courses = recs.get("courses", [])
        recommended_certs = recs.get("certifications", [])

    app = Application(
        candidate_id=candidate.id,
        job_id=job_id,
        status="applied",
        score=score,
        reason=reason,
        matched_skills=json.dumps(matched_s),
        missing_skills=json.dumps(missing_s),
        shap_values=json.dumps(shap_v),
        semantic_similarity=semantic_sim,
        recommended_courses=json.dumps(recommended_courses),
        recommended_certs=json.dumps(recommended_certs)
    )
    
    db.add(app)
    db.commit()
    db.refresh(app)

    return {
        "id": app.id,
        "candidate_id": app.candidate_id,
        "job_id": app.job_id,
        "status": app.status,
        "applied_date": app.created_at.isoformat() if app.created_at else None,
        "job_title": job.title,
        "company": "Resume AI",
        "location": "Remote",
        "salary": None
    }


@router.put("/applications/{application_id}/status")
def update_application_status_compat(application_id: str, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.status = status
    db.commit()
    return {"id": application_id, "status": status}


@router.get("/pipeline")
def list_pipeline_compat(job_id: str | None = None, recruiter_id: str | None = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    if not job_id:
        return []
        
    # Get all applications for this job
    apps = db.query(Application).filter(Application.job_id == job_id).all()
    if not apps:
        return []

    # Map to Pipeline candidates list to rank them using XGBoost dynamically
    ai_service = AIService()
    cand_payloads = []
    app_mapping = {}
    
    for app in apps:
        candidate = app.candidate
        if not candidate:
            continue
        resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.uploaded_at.desc()).first()
        raw_text = resume.raw_text if resume else ""
        
        payload = {
            "id": app.id,
            "application_id": app.id,
            "candidate_id": candidate.id,
            "resume_text": raw_text,
            "raw_text": raw_text,
            "status": app.status,
            "created_at": app.created_at,
            "name": candidate.user.name if candidate.user else "Candidate Profile",
            "location": candidate.location or "Remote",
            "experience": candidate.experience or "No experience",
            "job_description": app.job.description if app.job else ""
        }
        cand_payloads.append(payload)
        app_mapping[app.id] = app

    # Rank them
    ranked_payloads = ai_service.rank_candidates(cand_payloads, app.job.description if app.job else "")
    
    # Save/update ranks in DB
    for r in ranked_payloads:
        app = app_mapping.get(r["application_id"])
        if app:
            app.rank = r["rank"]
            app.top_match = r["top_match"]
            app.score = int(round(r["rank_score"] * 100))
            db.commit()

    # Paginate results
    start = (page - 1) * page_size
    end = start + page_size
    paginated = ranked_payloads[start:end]

    results = []
    for r in paginated:
        app = app_mapping.get(r["application_id"])
        
        # Parse fields
        matched = []
        missing = []
        if app.matched_skills:
            matched = json.loads(app.matched_skills)
        if app.missing_skills:
            missing = json.loads(app.missing_skills)
            
        results.append({
            "id": app.id,
            "recruiter_id": 1,
            "job_id": app.job_id,
            "candidate_id": app.candidate_id,
            "profile_id": app.candidate_id,
            "score": app.score,
            "rank": app.rank or r["rank"],
            "top_match": app.top_match,
            "reason": app.reason or r.get("summary", {}).get("summary"),
            "status": app.status,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "name": r["name"],
            "role": app.job.title if app.job else "Software Engineer",
            "location": r["location"],
            "experience": r["experience"],
            "summary": r.get("summary", {}).get("summary") or app.reason,
            "matched": matched,
            "missing": missing
        })

    return results


@router.get("/pipeline/count")
def count_pipeline_compat(job_id: str | None = None, recruiter_id: str | None = None, db: Session = Depends(get_db)):
    if not job_id:
        return {"total": 0}
    total = db.query(Application).filter(Application.job_id == job_id).count()
    return {"total": total}


@router.put("/pipeline/{pipeline_id}/status")
def update_pipeline_status_compat(pipeline_id: str, payload: dict[str, Any], db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == pipeline_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Pipeline application not found")
    app.status = payload.get("status", "applied")
    db.commit()
    return {"id": pipeline_id, "status": app.status}


@router.post("/pipeline/ingest-pdf")
def ingest_pdf_compat(job_id: str | None = None, file: UploadFile = File(...), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 1. Create a standalone profile (Requires generating a unique user first)
    unique_id = str(uuid4())
    dummy_user = User(
        name=f"Ingested Candidate",
        email=f"ingested-{unique_id}@cvlect-ai.recruitment",
        hashed_password=f"no-login-for-ingested-{unique_id}",
        role="Candidate"
    )
    db.add(dummy_user)
    db.commit()
    db.refresh(dummy_user)

    candidate = Candidate(
        user_id=dummy_user.id,
        experience="No experience parsed yet",
        skills=""
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # 2. Process the uploaded resume
    filename, filepath = FileHandler.save_upload(file)
    ai_service = AIService()
    ai_result = ai_service.process_resume(filepath, job_description=job.description)
    
    parsed = ai_result.get("parsed", {})
    features = ai_result.get("features", {})
    fraud = ai_result.get("fraud_report", {})
    bias = ai_result.get("bias_report", {})
    summary = ai_result.get("summary", {})

    # Save resume
    resume = Resume(
        candidate_id=candidate.id,
        filename=filename,
        filepath=filepath,
        ats_score=ai_result["ats_score"],
        match_percentage=ai_result["match_percentage"],
        status="uploaded",
        raw_text=ai_result.get("text"),
        skills_list=json.dumps(parsed.get("skills", [])),
        experience_years=parsed.get("experience_years", 0),
        parsed_education=json.dumps(parsed.get("education", [])),
        parsed_projects=json.dumps(parsed.get("projects", [])),
        parsed_certifications=json.dumps(parsed.get("certifications", [])),
        summary=summary.get("summary"),
        fraud_score=fraud.get("risk_score"),
        fraud_warnings=json.dumps(fraud.get("warnings", [])),
        bias_score=bias.get("bias_score"),
        bias_flagged_terms=json.dumps(bias.get("flagged_terms", []))
    )
    db.add(resume)
    
    # Save parsed experience details back to Candidate
    candidate.experience = f"{parsed.get('experience_years', 0)} years"
    candidate.skills = ", ".join(parsed.get("skills", []))
    if parsed.get("education"):
        candidate.education = ", ".join(parsed.get("education"))
    
    # Update candidate display name to show parsed name
    dummy_user.name = parsed.get("name", "Ingested Candidate")

    # 3. Create Application match record
    skills = {s.lower() for s in parsed.get("skills", [])}
    job_skills = ai_service.recommender._extract_skills_from_text(job.description.lower())
    matched_s = list(skills & job_skills)
    missing_s = list(job_skills - skills)
    
    recs = ai_service.recommend([{"parsed_resume": parsed, "job_description": job.description}], limit=1)[0].get("recommendations", {})

    app = Application(
        candidate_id=candidate.id,
        job_id=job_id,
        status="applied",
        score=ai_result["match_percentage"],
        reason=summary.get("summary"),
        matched_skills=json.dumps(matched_s),
        missing_skills=json.dumps(missing_s),
        shap_values=json.dumps(ai_result.get("explanation", {}).get("shap_values", {})),
        semantic_similarity=float(features.get("semantic_similarity", 0.0)),
        recommended_courses=json.dumps(recs.get("courses", [])),
        recommended_certs=json.dumps(recs.get("certifications", []))
    )
    db.add(app)
    db.commit()

    return {
        "message": "Resume ingested",
        "user_id": dummy_user.id,
        "profile_id": candidate.id
    }


@router.get("/stats")
def get_stats_compat(recruiter_id: str | None = None, job_id: str | None = None, db: Session = Depends(get_db)):
    """Get dashboard stats for recruiter."""
    from app.models.application import Application
    from app.models.job import Job
    from app.models.candidate import Candidate
    
    # Base query for applications
    query = db.query(Application)
    
    if job_id:
        query = query.filter(Application.job_id == job_id)
    elif recruiter_id:
        # Get jobs for this recruiter (recruiter_id is a UUID string)
        job_ids = db.query(Job.id).filter(Job.recruiter_id == recruiter_id).all()
        job_ids = [j[0] for j in job_ids]
        if job_ids:
            query = query.filter(Application.job_id.in_(job_ids))
    
    total = query.count()
    shortlisted = query.filter(Application.status == "shortlisted").count()
    selected = query.filter(Application.status == "selected").count()
    rejected = query.filter(Application.status == "rejected").count()
    
    return {
        "total_resumes": total,
        "shortlisted": shortlisted,
        "selected": selected,
        "rejected": rejected
    }


@router.get("/activities")
def list_activities_compat(recruiter_id: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    """Get recent activities for recruiter dashboard."""
    from app.models.application import Application
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.models.user import User
    
    # Get recent applications with related data
    query = db.query(Application).order_by(Application.created_at.desc()).limit(limit)
    
    if recruiter_id:
        # recruiter_id is a UUID string, not an integer
        job_ids = db.query(Job.id).filter(Job.recruiter_id == recruiter_id).all()
        job_ids = [j[0] for j in job_ids]
        if job_ids:
            query = query.filter(Application.job_id.in_(job_ids))
    
    activities = []
    for app in query.all():
        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
        job = db.query(Job).filter(Job.id == app.job_id).first()
        user = db.query(User).filter(User.id == candidate.user_id).first() if candidate else None
        
        if app.status == "applied":
            text = f"{user.name if user else 'A candidate'} applied to {job.title if job else 'a position'}"
        elif app.status == "shortlisted":
            text = f"{user.name if user else 'A candidate'} was shortlisted for {job.title if job else 'a position'}"
        elif app.status == "selected":
            text = f"{user.name if user else 'A candidate'} was selected for {job.title if job else 'a position'}"
        elif app.status == "rejected":
            text = f"{user.name if user else 'A candidate'} was rejected for {job.title if job else 'a position'}"
        else:
            text = f"Application status updated to {app.status}"
        
        activities.append({
            "id": app.id,
            "recruiter_id": recruiter_id,
            "text": text,
            "created_at": app.created_at.isoformat() if app.created_at else None
        })
    
    return activities
