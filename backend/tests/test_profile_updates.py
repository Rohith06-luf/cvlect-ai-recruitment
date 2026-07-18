from app.routes import compat


def test_build_profile_update_payload_maps_user_and_candidate_fields() -> None:
    payload = {
        "name": "Ada Lovelace",
        "location": "London",
        "experience": "5 years",
        "summary": "Full-stack engineer",
        "phone": "+44 1234",
        "skills": "Python, FastAPI",
        "company": "CVlect",
        "job_title": "Principal Engineer",
        "team": "AI Platform",
        "about": "Building recruiter workflows",
    }

    update_payload = compat._build_profile_update_payload(payload)

    assert update_payload["user_data"]["name"] == "Ada Lovelace"
    assert update_payload["user_data"]["company"] == "CVlect"
    assert update_payload["candidate_data"]["location"] == "London"
    assert update_payload["candidate_data"]["experience"] == "5 years"
    assert update_payload["candidate_data"]["skills"] == "Python, FastAPI"
    assert update_payload["candidate_data"]["summary"] == "Full-stack engineer"
