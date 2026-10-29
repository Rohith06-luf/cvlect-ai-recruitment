"""
CVlect AI — Candidate-Job Matching Engine
Implements the 5-stage explainable matching pipeline:
  Stage A: Structured Extraction
  Stage B: Dense Vector Representation & Cosine Similarity
  Stage C: Multi-Factor Feature Engineering
  Stage D: Neural Ranking or Transparent Weighted Baseline
  Stage E: Calibration, Evidence Mapping & Score Synthesis
"""

from typing import Optional, Any
import numpy as np
from sqlalchemy.orm import Session

from app.models.models import ExtractedResumeData, Job, MatchResult
from app.services.embedding_service import (
    generate_embedding,
    cosine_similarity,
    bytes_to_embedding,
)
from app.services.nlp_engine import compute_skill_overlap, normalize_skill
from app.utils import get_logger

logger = get_logger(__name__)

# Configurable weights for weighted baseline scoring
SCORE_WEIGHTS: dict[str, float] = {
    "skill": 0.30,
    "semantic": 0.25,
    "experience": 0.20,
    "education": 0.10,
    "project": 0.15,
}


def compute_skill_alignment(
    resume_skills: list[str],
    job_required: list[str],
    job_preferred: list[str],
) -> tuple[float, float, list[str], list[str], list[str], list[str]]:
    """
    Calculate skill alignment metrics.
    Returns:
        (skill_score, pref_score, matched_req, missing_req, partial_req, matched_pref)
    """
    matched_req, missing_req, partial_req = compute_skill_overlap(
        resume_skills=resume_skills,
        required_skills=job_required or [],
    )

    matched_pref, _, _ = compute_skill_overlap(
        resume_skills=resume_skills,
        required_skills=job_preferred or [],
    )

    # Required skills score
    if not job_required:
        # If no specific required skills, default score based on sheer skill count
        req_score = min(100.0, len(resume_skills) * 8.0)
    else:
        full_pts = len(matched_req) * 1.0
        part_pts = len(partial_req) * 0.5
        req_score = ((full_pts + part_pts) / len(job_required)) * 100.0

    # Preferred skills score
    pref_score = 100.0 if not job_preferred else (len(matched_pref) / len(job_preferred)) * 100.0

    # Composite skill score with bonus for preferred skills
    final_skill_score = min(100.0, (req_score * 0.85) + (pref_score * 0.15))
    return (
        round(final_skill_score, 1),
        round(pref_score, 1),
        matched_req,
        missing_req,
        partial_req,
        matched_pref,
    )


def compute_experience_alignment(
    candidate_years: float,
    job_min: int,
    job_max: int,
) -> float:
    """Evaluate experience alignment on a 0-100 scale."""
    if job_min == 0 and candidate_years >= 0:
        return 100.0

    if candidate_years >= job_min:
        if job_max > 0 and candidate_years > (job_max + 4):
            # Overqualification moderation
            return 90.0
        return 100.0
    else:
        ratio = candidate_years / max(1.0, float(job_min))
        # Scaled smoothly
        return round(max(15.0, ratio * 90.0), 1)


def compute_education_alignment(
    resume_education: list[dict],
    job_education_reqs: list[str],
) -> float:
    """Evaluate degree and academic background alignment."""
    if not job_education_reqs:
        return 90.0 if resume_education else 75.0

    if not resume_education:
        return 45.0

    degree_hierarchy = {
        "Ph.D.": 4,
        "Master's": 3,
        "Bachelor's": 2,
        "Associate's": 1,
        "Diploma": 1,
    }

    max_cand_level = max(
        [degree_hierarchy.get(e.get("degree", ""), 1) for e in resume_education],
        default=1,
    )

    req_hierarchy_level = 2  # default bachelor
    for req in job_education_reqs:
        req_lower = req.lower()
        if "ph.d" in req_lower or "doctorate" in req_lower:
            req_hierarchy_level = max(req_hierarchy_level, 4)
        elif "master" in req_lower or "m.s" in req_lower:
            req_hierarchy_level = max(req_hierarchy_level, 3)

    if max_cand_level >= req_hierarchy_level:
        return 100.0
    elif max_cand_level == req_hierarchy_level - 1:
        return 80.0
    else:
        return 60.0


def compute_project_alignment(
    projects: list[dict],
    required_skills: list[str],
    technologies: list[str],
) -> float:
    """Score the relevance and depth of practical projects."""
    if not projects:
        return 40.0

    target_tokens = {normalize_skill(s) for s in (required_skills + technologies) if s}
    if not target_tokens:
        return min(100.0, 50.0 + (len(projects) * 15.0))

    relevant_projects = 0
    for proj in projects:
        p_techs = {normalize_skill(t) for t in proj.get("technologies", []) if t}
        p_desc = (proj.get("description") or "").lower()
        matches = len(p_techs & target_tokens)
        desc_matches = sum(1 for tok in target_tokens if tok and tok in p_desc)

        if matches >= 1 or desc_matches >= 2:
            relevant_projects += 1

    if relevant_projects >= 2:
        return 95.0
    elif relevant_projects == 1:
        return 80.0
    else:
        return 60.0


def compute_semantic_alignment(
    resume_embedding: Optional[np.ndarray],
    job_embedding: Optional[np.ndarray],
    resume_text: str,
    job_desc: str,
) -> float:
    """Calculate dense vector similarity, falling back to dynamic embedding generation."""
    if resume_embedding is None and resume_text:
        resume_embedding = generate_embedding(resume_text[:2000])
    if job_embedding is None and job_desc:
        job_embedding = generate_embedding(job_desc[:2000])

    if resume_embedding is not None and job_embedding is not None:
        sim = cosine_similarity(resume_embedding, job_embedding)
        # Cosine similarity is usually in [0.2, 0.9] for relevant texts; scale gracefully
        scaled = max(0.0, (sim - 0.1) / 0.85) * 100.0
        return round(float(np.clip(scaled, 0.0, 100.0)), 1)

    # Fallback to Jaccard word token overlap
    r_words = set(resume_text.lower().split())
    j_words = set(job_desc.lower().split())
    if not j_words:
        return 50.0
    jaccard = len(r_words & j_words) / float(len(r_words | j_words))
    return round(min(100.0, jaccard * 250.0), 1)


# =============================================================================
# Core 5-Stage Match Function
# =============================================================================

def analyze_match(
    resume_data: ExtractedResumeData,
    job: Job,
    db: Session,
) -> MatchResult:
    """
    Execute the 5-stage matching pipeline:
      Stage A: Extraction (already completed on inputs)
      Stage B: Semantic embedding similarity
      Stage C: Feature engineering across skill, experience, project, education
      Stage D: Neural ranking model or transparent weighted baseline
      Stage E: Detailed explanation synthesis & DB persistence
    """
    # Stage A: Unpack structured representations
    resume_skills = resume_data.skills or []
    req_skills = job.required_skills or []
    pref_skills = job.preferred_skills or []
    experience_years = float(resume_data.total_experience_years or 0.0)
    education = resume_data.education or []
    projects = resume_data.projects or []

    # Stage B: Semantic dense similarity
    resume_emb = bytes_to_embedding(resume_data.embedding)
    job_emb = bytes_to_embedding(job.embedding)
    semantic_score = compute_semantic_alignment(
        resume_embedding=resume_emb,
        job_embedding=job_emb,
        resume_text=resume_data.raw_text or "",
        job_desc=job.description or "",
    )

    # Stage C: Engineer multi-dimensional features
    skill_score, pref_score, matched_req, missing_req, partial_req, matched_pref = compute_skill_alignment(
        resume_skills=resume_skills,
        job_required=req_skills,
        job_preferred=pref_skills,
    )

    experience_score = compute_experience_alignment(
        candidate_years=experience_years,
        job_min=job.experience_min or 0,
        job_max=job.experience_max or 99,
    )

    education_score = compute_education_alignment(
        resume_education=education,
        job_education_reqs=job.education_requirements or [],
    )

    project_score = compute_project_alignment(
        projects=projects,
        required_skills=req_skills,
        technologies=job.technologies or [],
    )

    # Feature vector normalized between 0 and 1 for machine learning
    feature_vector = {
        "skill_coverage": round(skill_score / 100.0, 4),
        "preferred_skill_coverage": round(pref_score / 100.0, 4),
        "semantic_similarity": round(semantic_score / 100.0, 4),
        "experience_alignment": round(experience_score / 100.0, 4),
        "education_alignment": round(education_score / 100.0, 4),
        "project_relevance": round(project_score / 100.0, 4),
    }

    feature_array = np.array([
        feature_vector["skill_coverage"],
        feature_vector["preferred_skill_coverage"],
        feature_vector["semantic_similarity"],
        feature_vector["experience_alignment"],
        feature_vector["education_alignment"],
        feature_vector["project_relevance"],
    ], dtype=np.float32)

    # Stage D: Apply Ranking Network or Weighted Baseline
    is_demo_mode = True
    scoring_method = "weighted_feature_combination"

    try:
        from app.ml.ranking_network import ranking_model_manager
        if ranking_model_manager.is_trained:
            pred_score = ranking_model_manager.predict(feature_array)
            if pred_score is not None:
                overall_score = round(float(pred_score) * 100.0, 1)
                is_demo_mode = False
                scoring_method = "neural_ranking_network"
            else:
                overall_score = round(
                    (skill_score * SCORE_WEIGHTS["skill"]) +
                    (semantic_score * SCORE_WEIGHTS["semantic"]) +
                    (experience_score * SCORE_WEIGHTS["experience"]) +
                    (education_score * SCORE_WEIGHTS["education"]) +
                    (project_score * SCORE_WEIGHTS["project"]),
                    1,
                )
        else:
            overall_score = round(
                (skill_score * SCORE_WEIGHTS["skill"]) +
                (semantic_score * SCORE_WEIGHTS["semantic"]) +
                (experience_score * SCORE_WEIGHTS["experience"]) +
                (education_score * SCORE_WEIGHTS["education"]) +
                (project_score * SCORE_WEIGHTS["project"]),
                1,
            )
    except Exception as e:
        logger.warning(f"Ranking model inference fallback: {e}")
        overall_score = round(
            (skill_score * SCORE_WEIGHTS["skill"]) +
            (semantic_score * SCORE_WEIGHTS["semantic"]) +
            (experience_score * SCORE_WEIGHTS["experience"]) +
            (education_score * SCORE_WEIGHTS["education"]) +
            (project_score * SCORE_WEIGHTS["project"]),
            1,
        )

    # Stage E: Produce Explanation, Recommendations, and Persist
    strong_matches = matched_req[:5] + matched_pref[:3]

    recommendations = []
    if missing_req:
        recommendations.append(f"Consider acquiring experience in: {', '.join(missing_req[:4])}")
    if experience_years < (job.experience_min or 0):
        recommendations.append(
            f"Role requires {job.experience_min} years; highlight practical project outcomes and contributions."
        )
    if not projects and (job.technologies or req_skills):
        recommendations.append("Add practical portfolio projects demonstrating skills required in the job.")

    # Feature contribution map
    contributions = {
        "skills": round(skill_score * SCORE_WEIGHTS["skill"], 1),
        "semantic": round(semantic_score * SCORE_WEIGHTS["semantic"], 1),
        "experience": round(experience_score * SCORE_WEIGHTS["experience"], 1),
        "projects": round(project_score * SCORE_WEIGHTS["project"], 1),
        "education": round(education_score * SCORE_WEIGHTS["education"], 1),
    }

    explanation_data = {
        "summary": (
            f"Candidate achieved an overall match of {overall_score}% for {job.title} at {job.company}. "
            f"Key strengths: {len(matched_req)} required skills matched. "
            f"Experience alignment is {experience_score}% ({experience_years} years vs required {job.experience_min}-{job.experience_max} years)."
        ),
        "scoring_method": scoring_method,
        "is_demo_mode": is_demo_mode,
        "feature_contributions": contributions,
        "weights": SCORE_WEIGHTS,
        "matched_skills": matched_req,
        "missing_skills": missing_req,
        "partially_matched": partial_req,
        "strong_matches": strong_matches,
        "recommendations": recommendations,
        "evidence": [
            {"factor": "Skills", "detail": f"Matched {len(matched_req)}/{len(req_skills or [1])} required skills"},
            {"factor": "Experience", "detail": f"{experience_years} yrs verified against {job.experience_min}-{job.experience_max} yrs"},
            {"factor": "Education", "detail": f"Evaluated {len(education)} educational record(s)"},
        ],
    }

    # Upsert MatchResult record in database
    existing_match = (
        db.query(MatchResult)
        .filter(MatchResult.resume_id == resume_data.resume_id, MatchResult.job_id == job.id)
        .first()
    )

    if existing_match:
        existing_match.overall_score = overall_score
        existing_match.skill_score = skill_score
        existing_match.experience_score = experience_score
        existing_match.education_score = education_score
        existing_match.semantic_score = semantic_score
        existing_match.project_score = project_score
        existing_match.feature_vector = feature_vector
        existing_match.explanation = explanation_data
        existing_match.matched_skills = matched_req
        existing_match.missing_skills = missing_req
        existing_match.partially_matched = partial_req
        existing_match.strong_matches = strong_matches
        existing_match.recommendations = recommendations
        existing_match.is_demo_mode = is_demo_mode
        match_record = existing_match
    else:
        match_record = MatchResult(
            resume_id=resume_data.resume_id,
            job_id=job.id,
            overall_score=overall_score,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            semantic_score=semantic_score,
            project_score=project_score,
            feature_vector=feature_vector,
            explanation=explanation_data,
            matched_skills=matched_req,
            missing_skills=missing_req,
            partially_matched=partial_req,
            strong_matches=strong_matches,
            recommendations=recommendations,
            is_demo_mode=is_demo_mode,
        )
        db.add(match_record)

    db.commit()
    db.refresh(match_record)
    return match_record


def batch_match_resume_to_jobs(
    resume_data: ExtractedResumeData,
    jobs: list[Job],
    db: Session,
) -> list[MatchResult]:
    """Execute match pipeline for a single resume across multiple job listings."""
    results = []
    for job in jobs:
        try:
            match_res = analyze_match(resume_data=resume_data, job=job, db=db)
            results.append(match_res)
        except Exception as e:
            logger.error(f"Failed to match resume {resume_data.resume_id} to job {job.id}: {e}")
            db.rollback()
    return sorted(results, key=lambda m: m.overall_score, reverse=True)


def batch_match_job_to_resumes(
    job: Job,
    resume_data_list: list[ExtractedResumeData],
    db: Session,
) -> list[MatchResult]:
    """Rank multiple candidate resumes against a single job listing."""
    results = []
    for r_data in resume_data_list:
        try:
            match_res = analyze_match(resume_data=r_data, job=job, db=db)
            results.append(match_res)
        except Exception as e:
            logger.error(f"Failed to match candidate resume {r_data.resume_id} to job {job.id}: {e}")
            db.rollback()
    return sorted(results, key=lambda m: m.overall_score, reverse=True)
