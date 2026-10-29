"""
CVlect AI — Analytics API Endpoints
Real database-driven analytics for candidate performance, recruiter pipelines,
and diagnostic fairness audits.
"""

from collections import Counter
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import Resume, Job, Application, MatchResult, User, ExtractedResumeData
from app.schemas.schemas import CandidateAnalytics, RecruiterAnalytics, FairnessReport
from app.services.auth_service import require_candidate, require_recruiter
from app.services.fairness import generate_fairness_report
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/candidate", response_model=CandidateAnalytics)
def get_candidate_analytics(
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """
    Compute live candidate dashboard metrics directly from PostgreSQL/SQLite.
    """
    # 1. Resume Metrics
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    total_resumes = len(resumes)
    analyzed_resumes = sum(1 for r in resumes if r.is_analyzed)
    resume_ids = [r.id for r in resumes]

    # 2. Application Metrics
    applications = (
        db.query(Application)
        .filter(Application.candidate_id == current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    total_applications = len(applications)

    app_counts: dict[str, int] = {}
    for a in applications:
        app_counts[a.status] = app_counts.get(a.status, 0) + 1

    # 3. Match Scores
    matches = (
        db.query(MatchResult)
        .filter(MatchResult.resume_id.in_(resume_ids))
        .all()
        if resume_ids else []
    )

    scores = [m.overall_score for m in matches if m.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    top_score = round(max(scores), 1) if scores else 0.0

    # 4. Top Skills & Skill Gaps
    all_skills = []
    for r in resumes:
        if r.extracted_data and r.extracted_data.skills:
            all_skills.extend(r.extracted_data.skills)
    skill_counts = Counter(all_skills)
    top_skills = [s for s, _ in skill_counts.most_common(8)]

    missing_skills = []
    for m in matches:
        if m.missing_skills:
            missing_skills.extend(m.missing_skills)
    gap_counts = Counter(missing_skills)
    top_gaps = [g for g, _ in gap_counts.most_common(5)]

    # 5. Recent Activity
    recent_activity = []
    for a in applications[:5]:
        recent_activity.append({
            "action": f"Applied for {a.job.title if a.job else 'Position'}",
            "company": a.job.company if a.job else "Company",
            "status": a.status,
            "date": a.applied_at.isoformat() if a.applied_at else None,
        })

    return CandidateAnalytics(
        total_resumes=total_resumes,
        analyzed_resumes=analyzed_resumes,
        total_applications=total_applications,
        applications_by_status=app_counts,
        avg_match_score=avg_score,
        top_match_score=top_score,
        top_skills=top_skills,
        skill_gaps=top_gaps,
        recent_activity=recent_activity,
    )


@router.get("/recruiter", response_model=RecruiterAnalytics)
def get_recruiter_analytics(
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """
    Compute live recruiter recruitment pipeline metrics directly from database.
    """
    # 1. Job Metrics
    jobs = db.query(Job).filter(Job.recruiter_id == current_user.id).all()
    total_jobs = len(jobs)
    active_jobs = sum(1 for j in jobs if j.status == "active")
    job_ids = [j.id for j in jobs]

    # 2. Application Metrics
    applications = (
        db.query(Application)
        .filter(Application.job_id.in_(job_ids))
        .order_by(Application.applied_at.desc())
        .all()
        if job_ids else []
    )
    total_applications = len(applications)

    app_counts: dict[str, int] = {}
    for a in applications:
        app_counts[a.status] = app_counts.get(a.status, 0) + 1

    # 3. Match Analytics
    matches = (
        db.query(MatchResult)
        .filter(MatchResult.job_id.in_(job_ids))
        .all()
        if job_ids else []
    )
    scores = [m.overall_score for m in matches if m.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # 4. Pipeline Funnel Stats
    pipeline_stats = {
        "applied": app_counts.get("applied", 0),
        "reviewing": app_counts.get("reviewing", 0),
        "shortlisted": app_counts.get("shortlisted", 0),
        "interview": app_counts.get("interview", 0),
        "offered": app_counts.get("offered", 0),
        "rejected": app_counts.get("rejected", 0),
    }

    # 5. Skill Demand Distribution across Recruiter's jobs
    skills_in_demand = []
    for j in jobs:
        if j.required_skills:
            skills_in_demand.extend(j.required_skills)
    demand_counts = Counter(skills_in_demand)
    skill_distribution = dict(demand_counts.most_common(10))

    # 6. Recent Activity
    recent_activity = []
    for a in applications[:6]:
        cand = a.candidate
        recent_activity.append({
            "action": f"{cand.full_name if cand else 'Candidate'} applied",
            "job_title": a.job.title if a.job else "Role",
            "status": a.status,
            "date": a.applied_at.isoformat() if a.applied_at else None,
        })

    return RecruiterAnalytics(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        applications_by_status=app_counts,
        avg_match_score=avg_score,
        pipeline_stats=pipeline_stats,
        skill_distribution=skill_distribution,
        recent_activity=recent_activity,
    )


@router.get("/fairness/reports", response_model=FairnessReport)
@router.get("/fairness", response_model=FairnessReport, include_in_schema=False)
def get_fairness_report_endpoint(
    job_id: Optional[int] = None,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """
    Generate an algorithmic fairness & score distribution diagnostic report.
    Adheres strictly to statistical audit standards without inferring protected attributes.
    """
    query = db.query(MatchResult).join(Job, MatchResult.job_id == Job.id)

    if job_id:
        query = query.filter(Job.id == job_id, Job.recruiter_id == current_user.id)
    else:
        query = query.filter(Job.recruiter_id == current_user.id)

    match_results = query.all()

    # Fallback to system-wide matches if recruiter has very few matches yet
    if len(match_results) < 5:
        match_results = db.query(MatchResult).limit(100).all()

    report = generate_fairness_report(match_results=match_results)
    return report
