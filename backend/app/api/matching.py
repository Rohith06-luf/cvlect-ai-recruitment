"""
CVlect AI — Candidate-Job Matching API Endpoints
Pairwise analysis, candidate ranking for recruiters, job recommendations for candidates,
and in-depth explainability reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Resume, Job, MatchResult, User, ExtractedResumeData
from app.schemas.schemas import (
    MatchRequest,
    MatchResponse,
    MatchScoreBreakdown,
    MatchExplanation,
    CandidateRankingResponse,
    CandidateMatchItem,
    JobRecommendationResponse,
    JobMatchItem,
)
from app.services.auth_service import get_current_user, require_candidate, require_recruiter
from app.services.matching_engine import (
    analyze_match,
    batch_match_job_to_resumes,
    batch_match_resume_to_jobs,
)
from app.services.explainability import generate_explanation
from app.services.resume_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    parse_resume,
)
from app.services.embedding_service import generate_embedding, embedding_to_bytes
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/matching", tags=["Matching"])


def _ensure_resume_analyzed(resume: Resume, db: Session) -> ExtractedResumeData:
    """Helper to ensure extracted resume data is available prior to matching."""
    if resume.extracted_data:
        return resume.extracted_data

    # Parse and extract automatically
    raw_text = ""
    if resume.file_type == "pdf":
        raw_text = extract_text_from_pdf(resume.file_path)
    elif resume.file_type == "docx":
        raw_text = extract_text_from_docx(resume.file_path)

    parsed = parse_resume(raw_text)
    emb_arr = generate_embedding(raw_text[:2500])
    emb_bytes = embedding_to_bytes(emb_arr)

    extracted = ExtractedResumeData(
        resume_id=resume.id,
        raw_text=raw_text,
        contact_info=parsed.get("contact_info"),
        skills=parsed.get("skills"),
        technical_skills=parsed.get("technical_skills"),
        soft_skills=parsed.get("soft_skills"),
        education=parsed.get("education"),
        experience=parsed.get("experience"),
        certifications=parsed.get("certifications"),
        projects=parsed.get("projects"),
        keywords=parsed.get("keywords"),
        domain_knowledge=parsed.get("domain_knowledge"),
        total_experience_years=parsed.get("total_experience_years", 0.0),
        confidence_scores=parsed.get("confidence_scores"),
        missing_fields=parsed.get("missing_fields"),
        quality_score=parsed.get("quality_score", 0.0),
        quality_suggestions=parsed.get("quality_suggestions"),
        embedding=emb_bytes,
    )
    db.add(extracted)
    resume.is_analyzed = True
    db.commit()
    db.refresh(resume)
    return extracted


@router.post("/analyze", response_model=MatchResponse)
def match_resume_to_job(
    request_data: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run the 5-stage matching pipeline for an individual Resume and Job pair.
    Accessible to candidates for their resumes or recruiters for their job postings.
    """
    resume = db.query(Resume).filter(Resume.id == request_data.resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    job = db.query(Job).filter(Job.id == request_data.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found.")

    # Permissions
    if current_user.role == "candidate" and resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to candidate resume.")
    if current_user.role == "recruiter" and job.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to recruiter job.")

    extracted_data = _ensure_resume_analyzed(resume, db)
    match_result = analyze_match(resume_data=extracted_data, job=job, db=db)

    scores = MatchScoreBreakdown(
        overall_score=match_result.overall_score,
        skill_score=match_result.skill_score,
        experience_score=match_result.experience_score,
        education_score=match_result.education_score,
        semantic_score=match_result.semantic_score,
        project_score=match_result.project_score,
    )

    expl_dict = match_result.explanation or {}
    explanation = MatchExplanation(
        summary=expl_dict.get("summary"),
        matched_skills=match_result.matched_skills,
        missing_skills=match_result.missing_skills,
        partially_matched=match_result.partially_matched,
        strong_matches=match_result.strong_matches,
        recommendations=match_result.recommendations,
        feature_contributions=expl_dict.get("feature_contributions"),
        evidence=expl_dict.get("evidence"),
        scoring_method=expl_dict.get("scoring_method", "weighted_feature_combination"),
        is_demo_mode=match_result.is_demo_mode,
    )

    return MatchResponse(
        id=match_result.id,
        resume_id=match_result.resume_id,
        job_id=match_result.job_id,
        scores=scores,
        explanation=explanation,
        created_at=match_result.created_at,
    )


@router.get("/jobs/{job_id}/candidates", response_model=CandidateRankingResponse)
def get_ranked_candidates_for_job(
    job_id: int,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """
    Rank all available candidates against a recruiter's job posting.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.recruiter_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found or not owned by you.",
        )

    # Fetch candidate resumes with extracted data
    resumes = db.query(Resume).filter(Resume.is_analyzed == True).all()
    resume_data_list = [r.extracted_data for r in resumes if r.extracted_data is not None]

    matches = batch_match_job_to_resumes(job=job, resume_data_list=resume_data_list, db=db)

    items = []
    for m in matches:
        resume = m.resume
        user = resume.user if resume else None
        candidate_name = user.full_name if user else "Candidate"
        candidate_email = user.email if user else "candidate@example.com"

        items.append(CandidateMatchItem(
            resume_id=m.resume_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            overall_score=m.overall_score,
            skill_score=m.skill_score,
            experience_score=m.experience_score,
            matched_skills=m.matched_skills,
            missing_skills=m.missing_skills,
            is_demo_mode=m.is_demo_mode,
        ))

    return CandidateRankingResponse(
        job_id=job.id,
        job_title=job.title,
        candidates=items,
        total=len(items),
    )


@router.get("/resumes/{resume_id}/jobs", response_model=JobRecommendationResponse)
def get_recommended_jobs_for_resume(
    resume_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """
    Recommend and rank active jobs for a candidate's resume.
    """
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to you.",
        )

    extracted_data = _ensure_resume_analyzed(resume, db)
    active_jobs = db.query(Job).filter(Job.status == "active").all()

    matches = batch_match_resume_to_jobs(resume_data=extracted_data, jobs=active_jobs, db=db)

    items = []
    for m in matches:
        j = m.job
        if not j:
            continue
        items.append(JobMatchItem(
            job_id=j.id,
            job_title=j.title,
            company=j.company,
            location=j.location,
            work_mode=j.work_mode,
            overall_score=m.overall_score,
            skill_score=m.skill_score,
            matched_skills=m.matched_skills,
            missing_skills=m.missing_skills,
            is_demo_mode=m.is_demo_mode,
        ))

    return JobRecommendationResponse(
        resume_id=resume.id,
        jobs=items,
        total=len(items),
    )


@router.get("/{match_id}/explanation")
def get_match_explanation(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve comprehensive explainability report for a match outcome:
    attributions, evidence snippets, and recommendations.
    """
    match_result = db.query(MatchResult).filter(MatchResult.id == match_id).first()
    if not match_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match result not found.")

    resume = match_result.resume
    job = match_result.job

    # Authorization verification
    if current_user.role == "candidate" and resume and resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if current_user.role == "recruiter" and job and job.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if not resume or not resume.extracted_data or not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume extracted data or job record unavailable for explanation generation.",
        )

    explanation = generate_explanation(
        match_result=match_result,
        resume_data=resume.extracted_data,
        job=job,
    )
    return explanation
