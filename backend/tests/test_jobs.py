"""
CVlect AI — Jobs API Tests
Tests job creation, listing, updating, deletion, and role-based access restrictions.
"""

import pytest
from fastapi import status
from app.models.models import Job


def test_create_job(test_client, auth_headers_recruiter):
    """Recruiters can create new job postings with requirements."""
    payload = {
        "title": "Senior Python Backend Engineer",
        "company": "Apex Nexus Technologies",
        "description": "Looking for a seasoned backend engineer with 5+ years of experience in Python, FastAPI, and PostgreSQL.",
        "location": "San Francisco, CA",
        "work_mode": "hybrid",
        "experience_min": 5,
        "experience_max": 9,
        "salary_min": 130000,
        "salary_max": 170000,
        "required_skills": ["python", "fastapi", "postgresql", "docker"],
        "preferred_skills": ["aws", "redis"],
        "seniority": "senior",
        "category": "engineering",
        "status": "active",
    }

    response = test_client.post(
        "/api/jobs/",
        json=payload,
        headers=auth_headers_recruiter,
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["title"] == "Senior Python Backend Engineer"
    assert data["company"] == "Apex Nexus Technologies"
    assert "python" in data["required_skills"]
    assert data["experience_min"] == 5
    assert "id" in data


def test_candidate_cannot_create_job(test_client, auth_headers_candidate):
    """Candidates attempting to create a job posting receive 403 Forbidden."""
    payload = {
        "title": "Unauthorized Job Posting",
        "company": "Fake Corp",
        "description": "Attempting job creation with candidate credentials.",
    }

    response = test_client.post(
        "/api/jobs/",
        json=payload,
        headers=auth_headers_candidate,
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "recruiter" in response.json()["detail"].lower()


def test_list_jobs(test_client, test_db, test_user_recruiter):
    """Listing jobs returns paginated active postings."""
    # Seed 2 jobs
    j1 = Job(
        recruiter_id=test_user_recruiter.id,
        title="Full Stack Developer",
        company="Horizon Soft",
        description="Full stack React and Node.js engineer wanted.",
        work_mode="remote",
        status="active",
    )
    j2 = Job(
        recruiter_id=test_user_recruiter.id,
        title="Data Analyst",
        company="Insight Global",
        description="Data analyst with strong SQL skills.",
        work_mode="onsite",
        status="active",
    )
    test_db.add_all([j1, j2])
    test_db.commit()

    response = test_client.get("/api/jobs/", follow_redirects=True)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "items" in data
    assert data["total"] >= 2
    titles = [item["title"] for item in data["items"]]
    assert "Full Stack Developer" in titles
    assert "Data Analyst" in titles


def test_get_job(test_client, test_db, test_user_recruiter):
    """Retrieve details for a single job posting by ID."""
    job = Job(
        recruiter_id=test_user_recruiter.id,
        title="DevOps Lead",
        company="Cloud Vanguard",
        description="Lead DevOps engineer managing AWS EKS clusters.",
        work_mode="remote",
        required_skills=["aws", "kubernetes", "terraform"],
        status="active",
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    response = test_client.get(f"/api/jobs/{job.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == job.id
    assert data["title"] == "DevOps Lead"
    assert data["company"] == "Cloud Vanguard"


def test_update_job(test_client, test_db, test_user_recruiter, auth_headers_recruiter):
    """Recruiters can update job postings they own."""
    job = Job(
        recruiter_id=test_user_recruiter.id,
        title="Frontend Developer",
        company="WebCraft Studio",
        description="Frontend React developer role.",
        work_mode="onsite",
        status="active",
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    update_payload = {
        "title": "Senior Frontend Developer",
        "work_mode": "remote",
        "salary_min": 120000,
    }
    response = test_client.put(
        f"/api/jobs/{job.id}",
        json=update_payload,
        headers=auth_headers_recruiter,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["title"] == "Senior Frontend Developer"
    assert data["work_mode"] == "remote"
    assert data["salary_min"] == 120000


def test_delete_job(test_client, test_db, test_user_recruiter, auth_headers_recruiter):
    """Recruiters can delete job postings they own."""
    job = Job(
        recruiter_id=test_user_recruiter.id,
        title="Temporary Position",
        company="Ephemeral Systems",
        description="Position to be removed shortly.",
        status="active",
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    # Delete
    del_response = test_client.delete(
        f"/api/jobs/{job.id}",
        headers=auth_headers_recruiter,
    )
    assert del_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify not found
    get_response = test_client.get(f"/api/jobs/{job.id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
