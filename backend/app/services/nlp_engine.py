"""
CVlect AI — NLP Engine
Extracts structured job requirements, normalizes skill taxonomies,
and computes skill overlap metrics.
"""

import re
from typing import Any, Optional
from app.services.resume_parser import (
    ALL_TECH_SKILLS,
    SOFT_SKILLS_LIST,
    extract_skills,
    clean_text,
)
from app.utils import get_logger

logger = get_logger(__name__)

# Canonical skill aliasing dictionary
SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "k8s": "kubernetes",
    "k8": "kubernetes",
    "tf": "tensorflow",
    "torch": "pytorch",
    "postgres": "postgresql",
    "pg": "postgresql",
    "mongo": "mongodb",
    "aws": "amazon web services",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "nextjs": "next.js",
    "nuxtjs": "nuxt",
    "node": "node.js",
    "nodejs": "node.js",
    "express.js": "express",
    "expressjs": "express",
    "fastapi": "fastapi",
    "spring": "spring boot",
    "dotnet": ".net",
    "sklearn": "scikit-learn",
    "rest": "restful api",
    "rest api": "restful api",
    "restful": "restful api",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "big query": "bigquery",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill token by trimming, lowercasing, and resolving canonical aliases."""
    if not skill:
        return ""
    cleaned = skill.strip().lower()
    cleaned = re.sub(r'^[^\w.#+]+|[^\w.#+]+$', '', cleaned)
    return SKILL_ALIASES.get(cleaned, cleaned)


def compute_skill_overlap(
    resume_skills: list[str],
    required_skills: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """
    Compare resume skills against required job skills.
    Returns:
        (matched_skills, missing_skills, partially_matched_skills)
    """
    if not required_skills:
        return sorted(list(set(resume_skills))), [], []

    norm_resume_skills = {normalize_skill(s): s for s in resume_skills if s}
    norm_required_skills = {normalize_skill(s): s for s in required_skills if s}

    matched: set[str] = set()
    partial: set[str] = set()
    missing: set[str] = set()

    for norm_req, original_req in norm_required_skills.items():
        if not norm_req:
            continue

        # Exact normalized match
        if norm_req in norm_resume_skills:
            matched.add(original_req)
            continue

        # Substring / partial match heuristic
        found_partial = False
        for norm_cand in norm_resume_skills.keys():
            if (len(norm_req) >= 4 and norm_req in norm_cand) or (len(norm_cand) >= 4 and norm_cand in norm_req):
                partial.add(original_req)
                found_partial = True
                break

        if not found_partial:
            missing.add(original_req)

    return sorted(list(matched)), sorted(list(missing)), sorted(list(partial))


# =============================================================================
# Job Requirements Extraction
# =============================================================================

def extract_job_requirements(job_description: str) -> dict[str, Any]:
    """
    Parse a raw job description into structured requirements:
    - required_skills
    - preferred_skills
    - experience_requirements (min_years, max_years)
    - education
    - certifications
    - responsibilities
    - technologies
    - seniority
    - category
    """
    text = clean_text(job_description)
    lines = text.split("\n")

    required_section_lines = []
    preferred_section_lines = []
    responsibilities_lines = []

    current_section = "general"

    for line in lines:
        stripped = line.strip()
        lower_line = stripped.lower()

        # Section detection
        if re.search(r'^(?:requirements|qualifications|must have|what you need|what you\'ll bring|basic qualifications)\b', lower_line):
            current_section = "required"
            continue
        elif re.search(r'^(?:preferred|nice to have|bonus|desired|preferred qualifications|what gives you an edge)\b', lower_line):
            current_section = "preferred"
            continue
        elif re.search(r'^(?:responsibilities|what you\'ll do|key duties|the role|what you will be doing)\b', lower_line):
            current_section = "responsibilities"
            continue
        elif re.search(r'^(?:benefits|perks|about us|company overview|compensation)\b', lower_line):
            current_section = "other"
            continue

        if current_section == "required":
            required_section_lines.append(stripped)
        elif current_section == "preferred":
            preferred_section_lines.append(stripped)
        elif current_section == "responsibilities":
            responsibilities_lines.append(stripped)

    # 1. Experience Years
    exp_min = 0
    exp_max = 99
    exp_match_range = re.search(r'(\d+)\s*(?:-|–|to)\s*(\d+)\+?\s*years?', text, re.IGNORECASE)
    if exp_match_range:
        exp_min = int(exp_match_range.group(1))
        exp_max = int(exp_match_range.group(2))
    else:
        exp_match_single = re.search(r'(\d+)\+?\s*years?(?:\s+of)?(?:\s+(?:relevant|hands-on|industry|work))?\s+experience', text, re.IGNORECASE)
        if exp_match_single:
            exp_min = int(exp_match_single.group(1))
            exp_max = max(exp_min + 3, 5)

    # 2. Skills Extraction
    req_text = "\n".join(required_section_lines) if required_section_lines else text
    pref_text = "\n".join(preferred_section_lines)

    all_req_skills, req_tech, _ = extract_skills(req_text)
    all_pref_skills, pref_tech, _ = extract_skills(pref_text) if pref_text else ([], [], [])

    # Exclude skills already in required from preferred
    preferred_skills = [s for s in all_pref_skills if s not in all_req_skills]
    technologies = sorted(list(set(req_tech + pref_tech)))

    # 3. Education
    education_reqs = []
    edu_patterns = [
        (r'\b(Ph\.?D\.?|Doctorate)\b', "Ph.D. in Computer Science or related field"),
        (r'\b(Master\'?s|M\.?S\.?|M\.?Tech)\b', "Master's degree in Computer Science, Engineering, or related field"),
        (r'\b(Bachelor\'?s|B\.?S\.?|B\.?Tech|B\.?E\.?)\b', "Bachelor's degree in Computer Science, Engineering, or related technical field"),
    ]
    for pattern, desc in edu_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            education_reqs.append(desc)

    if not education_reqs and re.search(r'\b(?:degree|computer science|stem|engineering)\b', text, re.IGNORECASE):
        education_reqs.append("Degree in Computer Science, STEM, or equivalent practical experience")

    # 4. Certifications
    certs = []
    cert_matches = [
        "aws certified", "azure certified", "gcp certified", "pmp", "cissp", "cka", "scrum master"
    ]
    for c in cert_matches:
        if c in text.lower():
            certs.append(c.upper())

    # 5. Responsibilities
    responsibilities = []
    if responsibilities_lines:
        for r_line in responsibilities_lines:
            cleaned_bullet = re.sub(r'^[•\-\*]\s*', '', r_line).strip()
            if len(cleaned_bullet) > 20:
                responsibilities.append(cleaned_bullet)
    else:
        # Fallback: extract bullet lines from overall text
        for line in lines:
            line_str = line.strip()
            if (line_str.startswith("•") or line_str.startswith("-") or line_str.startswith("*")) and len(line_str) > 25:
                cleaned_b = re.sub(r'^[•\-\*]\s*', '', line_str).strip()
                responsibilities.append(cleaned_b)
                if len(responsibilities) >= 6:
                    break

    # 6. Seniority
    seniority = "mid"
    title_first_para = "\n".join(lines[:5]).lower()
    if any(k in title_first_para for k in ["intern", "internship"]):
        seniority = "intern"
    elif any(k in title_first_para for k in ["junior", "jr", "entry level", "associate", "graduate"]):
        seniority = "junior"
    elif any(k in title_first_para for k in ["principal", "distinguished", "fellow"]):
        seniority = "principal"
    elif any(k in title_first_para for k in ["lead", "staff", "head of", "director", "manager"]):
        seniority = "lead"
    elif any(k in title_first_para for k in ["senior", "sr."]):
        seniority = "senior"

    # 7. Job Category
    category = "Software Engineering"
    desc_lower = text.lower()
    if any(k in desc_lower for k in ["data scientist", "machine learning", "deep learning", "ai engineer", "data engineer"]):
        category = "Data Science & AI"
    elif any(k in desc_lower for k in ["devops", "cloud engineer", "site reliability", "sre", "infrastructure", "kubernetes"]):
        category = "Cloud & DevOps"
    elif any(k in desc_lower for k in ["frontend", "front-end", "ui engineer", "react", "vue"]):
        category = "Frontend Engineering"
    elif any(k in desc_lower for k in ["backend", "back-end", "api developer", "microservices"]):
        category = "Backend Engineering"
    elif any(k in desc_lower for k in ["security", "cybersecurity", "infosec", "penetration"]):
        category = "Cybersecurity"
    elif any(k in desc_lower for k in ["product manager", "scrum master", "project manager"]):
        category = "Product Management"
    elif any(k in desc_lower for k in ["qa engineer", "test engineer", "automation tester"]):
        category = "Quality Assurance"

    return {
        "required_skills": all_req_skills,
        "preferred_skills": preferred_skills,
        "experience_requirements": {
            "min_years": exp_min,
            "max_years": exp_max,
            "summary": f"{exp_min}-{exp_max} years" if exp_max < 99 else f"{exp_min}+ years",
        },
        "education": education_reqs,
        "certifications": certs,
        "responsibilities": responsibilities[:10],
        "technologies": technologies,
        "seniority": seniority,
        "category": category,
    }
