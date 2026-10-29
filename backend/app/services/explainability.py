"""
CVlect AI — Explainability & Interpretability Service
Provides feature attribution, evidence linking against source texts,
SHAP analysis (when available), and plain-language transparent breakdowns.
"""

import re
from typing import Any, Optional
import numpy as np

from app.models.models import MatchResult, ExtractedResumeData, Job
from app.services.matching_engine import SCORE_WEIGHTS
from app.utils import get_logger

logger = get_logger(__name__)


def compute_shap_contributions(
    feature_vector_dict: dict[str, float],
) -> Optional[dict[str, float]]:
    """
    Attempt SHAP value calculation for the neural ranking network.
    Gracefully falls back to None if SHAP or PyTorch is unavailable.
    """
    try:
        import shap
        from app.ml.ranking_network import ranking_model_manager
        if not ranking_model_manager.is_trained:
            return None

        features = np.array([[
            feature_vector_dict.get("skill_coverage", 0.0),
            feature_vector_dict.get("preferred_skill_coverage", 0.0),
            feature_vector_dict.get("semantic_similarity", 0.0),
            feature_vector_dict.get("experience_alignment", 0.0),
            feature_vector_dict.get("education_alignment", 0.0),
            feature_vector_dict.get("project_relevance", 0.0),
        ]], dtype=np.float32)

        # Baseline background distribution
        background = np.zeros((10, 6), dtype=np.float32)
        explainer = shap.KernelExplainer(ranking_model_manager.predict, background)
        shap_values = explainer.shap_values(features, nsamples=50)

        if isinstance(shap_values, list):
            vals = shap_values[0].flatten()
        else:
            vals = np.asarray(shap_values).flatten()

        keys = [
            "skill_coverage",
            "preferred_skill_coverage",
            "semantic_similarity",
            "experience_alignment",
            "education_alignment",
            "project_relevance",
        ]
        return {k: round(float(vals[i]), 4) for i, k in enumerate(keys)}
    except Exception as e:
        logger.debug(f"SHAP computation skipped or failed ({e}); using weighted attributions.")
        return None


def find_text_evidence(
    term: str,
    text: str,
    max_len: int = 140,
) -> Optional[str]:
    """Locate a snippet from source text where the given term appears."""
    if not term or not text:
        return None

    pattern = rf'([^.?!;\n]*?\b{re.escape(term)}\b[^.?!;\n]*)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        snippet = match.group(0).strip()
        if len(snippet) > max_len:
            snippet = snippet[:max_len] + "..."
        return snippet
    return None


def generate_explanation(
    match_result: MatchResult,
    resume_data: ExtractedResumeData,
    job: Job,
) -> dict[str, Any]:
    """
    Synthesize complete explainability payload for candidate/recruiter inspection:
      1. Feature Contributions (SHAP or deterministic weights)
      2. Grounded evidence snippets from both resume and job description
      3. Plain-language transparent explanation narrative
      4. Clear distinction from LLM-generated summaries
    """
    raw_resume = resume_data.raw_text or ""
    raw_job = job.description or ""
    feat_vec = match_result.feature_vector or {}

    # 1. Feature Attribution
    shap_contribs = compute_shap_contributions(feat_vec)
    if shap_contribs:
        feature_contributions = shap_contribs
        attribution_method = "shap_kernel_attribution"
    else:
        # Transparent weighted contribution
        feature_contributions = {
            "skill_match": round((match_result.skill_score or 0.0) * SCORE_WEIGHTS["skill"], 1),
            "semantic_similarity": round((match_result.semantic_score or 0.0) * SCORE_WEIGHTS["semantic"], 1),
            "experience_match": round((match_result.experience_score or 0.0) * SCORE_WEIGHTS["experience"], 1),
            "project_depth": round((match_result.project_score or 0.0) * SCORE_WEIGHTS["project"], 1),
            "education_match": round((match_result.education_score or 0.0) * SCORE_WEIGHTS["education"], 1),
        }
        attribution_method = "linear_feature_weighting"

    # 2. Grounded Evidence Linking
    evidence: list[dict[str, Any]] = []

    # Evidence for top matched skills
    matched_skills = match_result.matched_skills or []
    for skill in matched_skills[:4]:
        r_snip = find_text_evidence(skill, raw_resume)
        j_snip = find_text_evidence(skill, raw_job)
        if r_snip or j_snip:
            evidence.append({
                "factor": f"Required Skill: {skill}",
                "status": "matched",
                "resume_snippet": r_snip or f"Extracted '{skill}' from profile",
                "job_snippet": j_snip or f"Listed as requirement in job description",
            })

    # Evidence for top missing skills
    missing_skills = match_result.missing_skills or []
    for skill in missing_skills[:3]:
        j_snip = find_text_evidence(skill, raw_job)
        evidence.append({
            "factor": f"Missing Skill: {skill}",
            "status": "missing",
            "resume_snippet": "Not detected in candidate profile",
            "job_snippet": j_snip or f"Required by role",
        })

    # Evidence for experience
    cand_years = resume_data.total_experience_years or 0.0
    evidence.append({
        "factor": "Experience Alignment",
        "status": "aligned" if cand_years >= (job.experience_min or 0) else "gap",
        "resume_snippet": f"Candidate has approximately {cand_years} years of verified experience",
        "job_snippet": f"Role specifies {job.experience_min} to {job.experience_max} years requirement",
    })

    # 3. Plain Language Narrative
    score = match_result.overall_score
    if score >= 80:
        verdict = "Strong Match"
        verdict_text = "Candidate profile strongly aligns with the core requirements and technical focus of this position."
    elif score >= 65:
        verdict = "Solid Match"
        verdict_text = "Candidate meets major requirements with good overall alignment, though some gaps or preferred skills are missing."
    elif score >= 50:
        verdict = "Moderate Match"
        verdict_text = "Candidate meets foundational qualifications but has notable skill or experience gaps."
    else:
        verdict = "Low Alignment"
        verdict_text = "Significant divergence between candidate's extracted profile and the role's mandatory requirements."

    matched_count = len(matched_skills)
    missing_count = len(missing_skills)

    narrative = (
        f"**{verdict} ({score}%)**: {verdict_text}\n\n"
        f"• **Technical Skills**: {matched_count} required skills verified ({', '.join(matched_skills[:5]) if matched_skills else 'None'}). "
        f"{missing_count} required skills were not detected ({', '.join(missing_skills[:4]) if missing_skills else 'None'}).\n"
        f"• **Experience**: Candidate possesses {cand_years} years against an expected range of {job.experience_min}–{job.experience_max} years.\n"
        f"• **Semantic Relevancy**: Conceptual profile similarity scored at {match_result.semantic_score}%."
    )

    return {
        "overall_score": score,
        "verdict": verdict,
        "narrative": narrative,
        "attribution_method": attribution_method,
        "feature_contributions": feature_contributions,
        "evidence": evidence,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "partially_matched": match_result.partially_matched or [],
        "recommendations": match_result.recommendations or [],
        "scoring_method": match_result.explanation.get("scoring_method", "weighted_baseline") if match_result.explanation else "weighted_baseline",
        "is_demo_mode": match_result.is_demo_mode,
        "explanation_type": "deterministic_algorithmic_explanation",
    }
