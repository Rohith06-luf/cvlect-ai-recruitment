"""
CVlect AI — Matching & Parser Tests
Unit tests for resume parsing heuristics, skill normalization, and 5-stage matching pipeline.
"""

import pytest
from app.services.resume_parser import parse_resume
from app.services.nlp_engine import normalize_skill, compute_skill_overlap
from app.services.matching_engine import analyze_match
from app.models.models import Resume, ExtractedResumeData, Job


def test_resume_parser_basic():
    """Verify parse_resume extracts contact info, skills, education, and experience from raw text."""
    sample_text = """
    Avery Sterling
    Email: avery.sterling@example.com
    Phone: (555) 234-5678
    Location: Seattle, WA
    LinkedIn: linkedin.com/in/avery-sterling-demo
    GitHub: github.com/avery-sterling-demo

    SUMMARY
    Senior full-stack engineer with 7+ years of experience building scalable microservices in Python and React on AWS.

    SKILLS
    Python, FastAPI, Django, React, TypeScript, Docker, Kubernetes, PostgreSQL, Redis, AWS, Git, Agile, Leadership

    EXPERIENCE
    Lead Full-Stack Engineer | Novasphere Cloud Systems
    2021 - Present
    - Architected scalable microservices handling 40M requests daily using FastAPI and PostgreSQL.
    - Mentored team of 5 software engineers and introduced automated testing standards.

    Senior Software Engineer | Beacon Peak Interactive
    2019 - 2021
    - Developed RESTful APIs and modern web applications with Python and React.

    EDUCATION
    Bachelor of Science in Computer Science
    Pacific Horizon University, 2017
    GPA: 3.85
    """

    parsed = parse_resume(sample_text)

    # Validate contact extraction
    assert parsed["contact_info"]["email"] == "avery.sterling@example.com"
    assert parsed["contact_info"]["phone"] == "(555) 234-5678"
    assert "avery" in parsed["contact_info"]["name"].lower()

    # Validate skill detection
    skills_lower = [s.lower() for s in parsed["skills"]]
    assert "python" in skills_lower
    assert "fastapi" in skills_lower
    assert "react" in skills_lower
    assert "docker" in skills_lower

    # Validate education extraction
    assert len(parsed["education"]) >= 1
    assert parsed["education"][0]["degree"] == "Bachelor's"

    # Validate experience detection & quality scoring
    assert len(parsed["experience"]) >= 1
    assert parsed["total_experience_years"] > 0
    assert parsed["quality_score"] > 60.0


def test_skill_normalization():
    """Verify canonical aliasing and skill token normalization."""
    # Canonical aliases mapping
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("reactjs") == "react"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("py") == "python"
    assert normalize_skill("js") == "javascript"
    assert normalize_skill("ts") == "typescript"
    assert normalize_skill("postgres") == "postgresql"
    assert normalize_skill("tf") == "tensorflow"

    # Overlap computation with aliases
    candidate_skills = ["reactjs", "python", "k8s", "docker"]
    required_skills = ["react", "python", "kubernetes", "aws"]

    matched, missing, partial = compute_skill_overlap(candidate_skills, required_skills)

    # "reactjs" normalizes to "react", "k8s" normalizes to "kubernetes"
    assert "react" in matched
    assert "python" in matched
    assert "kubernetes" in matched
    assert "aws" in missing


def test_matching_produces_score(test_db, test_user_candidate, test_user_recruiter):
    """Verify analyze_match runs the pipeline and persists a scored MatchResult record."""
    # 1. Create candidate resume & extracted data
    resume = Resume(
        user_id=test_user_candidate.id,
        filename="john_doe_resume.pdf",
        file_path="/tmp/john_doe.pdf",
        file_type="pdf",
        file_size=2048,
        is_analyzed=True,
    )
    test_db.add(resume)
    test_db.commit()
    test_db.refresh(resume)

    extracted = ExtractedResumeData(
        resume_id=resume.id,
        raw_text="Software engineer with Python, FastAPI, Docker, and PostgreSQL experience.",
        skills=["python", "fastapi", "docker", "postgresql", "redis"],
        technical_skills=["python", "fastapi", "docker", "postgresql"],
        education=[{"degree": "Bachelor's", "institution": "State University", "field": "CS"}],
        experience=[{"title": "Backend Engineer", "company": "Tech Corp", "description": "FastAPI dev"}],
        total_experience_years=4.0,
        quality_score=90.0,
    )
    test_db.add(extracted)

    # 2. Create recruiter job
    job = Job(
        recruiter_id=test_user_recruiter.id,
        title="Backend Python Engineer",
        company="Nexis Software",
        description="We are seeking a Backend Engineer with Python, FastAPI, and Docker skills.",
        experience_min=3,
        experience_max=6,
        required_skills=["python", "fastapi", "docker"],
        preferred_skills=["postgresql", "redis", "aws"],
        status="active",
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    # 3. Run matching pipeline
    match_result = analyze_match(resume_data=extracted, job=job, db=test_db)

    # Validate output structure and ranges
    assert match_result is not None
    assert 0.0 <= match_result.overall_score <= 100.0
    assert match_result.overall_score > 50.0  # High match expected given overlapping skills & experience
    assert match_result.skill_score > 70.0
    assert match_result.experience_score >= 80.0
    assert "python" in match_result.matched_skills
    assert "fastapi" in match_result.matched_skills
    assert "docker" in match_result.matched_skills
    assert match_result.explanation is not None
    assert "scoring_method" in match_result.explanation
    assert match_result.is_demo_mode in [True, False]
