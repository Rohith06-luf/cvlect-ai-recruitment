from app.services.ai_service import AIService


def test_skill_overlap_is_based_on_common_skills() -> None:
    service = AIService()

    resume_text = """
    John Doe
    Senior Python Engineer with 4 years of experience building APIs.
    Skills: Python, FastAPI, SQLAlchemy, Docker.
    """
    job_description = """
    We are hiring a backend engineer with strong Python, FastAPI, and Docker experience.
    """

    result = service.score_candidate(resume_text, job_description)

    assert result["features"]["skill_overlap"] > 0.5
    assert result["features"]["skill_overlap"] < 1.0
    assert result["summary"]["summary"]
    assert result["explanation"]["positive_features"]


def test_recommendation_engine_suggests_missing_skills() -> None:
    service = AIService()
    candidate = {
        "name": "Alice",
        "raw_text": "Python, SQL, REST APIs",
        "parsed_resume": {"skills": ["python", "sql"], "experience_years": 2},
        "job_description": "Python, FastAPI, Docker, AWS",
        "features": {"semantic_similarity": 0.8, "experience_years": 2, "education_score": 0.7, "skill_overlap": 0.6, "projects_score": 0.5, "certifications_score": 0.4},
    }

    result = service.recommend([candidate], limit=1)[0]

    assert result["recommendations"]["missing_skills"]
    assert result["recommendations"]["courses"]
    assert result["recommendations"]["certifications"]
