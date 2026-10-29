"""
CVlect AI — Resumes API Tests
Tests PDF/DOCX file uploading, format validation, candidate resume listings, and detail retrieval.
"""

import io
import pytest
from fastapi import status
from app.models.models import Resume, ExtractedResumeData

# Minimal valid 1-page PDF byte representation
MINIMAL_VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
)


def test_upload_resume_pdf(test_client, auth_headers_candidate):
    """Uploading a valid PDF resume creates a resume record with 201 status."""
    file_content = io.BytesIO(MINIMAL_VALID_PDF)
    files = {"file": ("test_resume.pdf", file_content, "application/pdf")}

    response = test_client.post(
        "/api/resumes/upload",
        files=files,
        headers=auth_headers_candidate,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["filename"] == "test_resume.pdf"
    assert data["file_type"] == "pdf"
    assert data["file_size"] > 0
    assert "id" in data


def test_upload_invalid_file_type(test_client, auth_headers_candidate):
    """Uploading an unsupported file format (e.g., .txt, .exe) returns 400 Bad Request."""
    file_content = io.BytesIO(b"Simple plain text resume content")
    files = {"file": ("resume.txt", file_content, "text/plain")}

    response = test_client.post(
        "/api/resumes/upload",
        files=files,
        headers=auth_headers_candidate,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "unsupported file format" in response.json()["detail"].lower()


def test_list_resumes(test_client, test_db, test_user_candidate, auth_headers_candidate):
    """Candidates can list their own uploaded resumes."""
    # Seed 2 resumes for candidate
    r1 = Resume(
        user_id=test_user_candidate.id,
        filename="first_resume.pdf",
        file_path="/tmp/first.pdf",
        file_type="pdf",
        file_size=1024,
        is_analyzed=False,
    )
    r2 = Resume(
        user_id=test_user_candidate.id,
        filename="second_resume.pdf",
        file_path="/tmp/second.pdf",
        file_type="pdf",
        file_size=2048,
        is_analyzed=True,
    )
    test_db.add_all([r1, r2])
    test_db.commit()

    response = test_client.get(
        "/api/resumes/",
        headers=auth_headers_candidate,
        follow_redirects=True,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2
    filenames = [r["filename"] for r in data]
    assert "first_resume.pdf" in filenames
    assert "second_resume.pdf" in filenames


def test_get_resume_detail(test_client, test_db, test_user_candidate, auth_headers_candidate):
    """Candidate can retrieve full details and extracted metadata for their resume."""
    resume = Resume(
        user_id=test_user_candidate.id,
        filename="software_engineer.pdf",
        file_path="/tmp/software_engineer.pdf",
        file_type="pdf",
        file_size=4096,
        is_analyzed=True,
    )
    test_db.add(resume)
    test_db.commit()
    test_db.refresh(resume)

    extracted = ExtractedResumeData(
        resume_id=resume.id,
        raw_text="Experienced Python and React Engineer",
        skills=["python", "react", "fastapi"],
        technical_skills=["python", "react"],
        soft_skills=["teamwork"],
        summary="Experienced engineer with 5 years in full-stack web development.",
        total_experience_years=5.0,
        quality_score=95.0,
    )
    test_db.add(extracted)
    test_db.commit()

    response = test_client.get(
        f"/api/resumes/{resume.id}",
        headers=auth_headers_candidate,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == resume.id
    assert data["filename"] == "software_engineer.pdf"
    assert data["is_analyzed"] is True
    assert data["extracted_data"] is not None
    assert "python" in data["extracted_data"]["skills"]
    assert data["extracted_data"]["quality_score"] == 95.0
