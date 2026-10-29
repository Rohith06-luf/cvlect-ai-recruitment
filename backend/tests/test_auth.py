"""
CVlect AI — Authentication & Authorization Tests
Tests registration, login validation, token issuance, and protected profile access.
"""

import pytest
from fastapi import status


def test_register_candidate(test_client):
    """Candidate registration successfully creates an account and returns a valid JWT token."""
    payload = {
        "email": "new.candidate@example.com",
        "password": "SecurePassword123!",
        "full_name": "New Candidate",
        "role": "candidate",
    }
    response = test_client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "new.candidate@example.com"
    assert data["user"]["role"] == "candidate"
    assert data["user"]["full_name"] == "New Candidate"
    assert "id" in data["user"]


def test_register_recruiter(test_client):
    """Recruiter registration creates an account with recruiter permissions."""
    payload = {
        "email": "new.recruiter@example.com",
        "password": "SecurePassword123!",
        "full_name": "New Recruiter",
        "role": "recruiter",
    }
    response = test_client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new.recruiter@example.com"
    assert data["user"]["role"] == "recruiter"


def test_register_duplicate_email(test_client, test_user_candidate):
    """Registering with an already existing email returns 409 Conflict."""
    payload = {
        "email": test_user_candidate.email,
        "password": "AnotherPassword123!",
        "full_name": "Duplicate User",
        "role": "candidate",
    }
    response = test_client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


def test_login_success(test_client, test_user_candidate):
    """Logging in with valid credentials yields a JWT bearer token."""
    payload = {
        "email": test_user_candidate.email,
        "password": "CandidateSecret123!",
    }
    response = test_client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == test_user_candidate.id
    assert data["user"]["email"] == test_user_candidate.email


def test_login_wrong_password(test_client, test_user_candidate):
    """Logging in with an incorrect password returns 401 Unauthorized."""
    payload = {
        "email": test_user_candidate.email,
        "password": "WrongPassword999!",
    }
    response = test_client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid email or password" in response.json()["detail"].lower()


def test_get_me_authenticated(test_client, test_user_candidate, auth_headers_candidate):
    """Authenticated user can successfully fetch their personal profile."""
    response = test_client.get("/api/auth/me", headers=auth_headers_candidate)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == test_user_candidate.id
    assert data["email"] == test_user_candidate.email
    assert data["role"] == "candidate"


def test_get_me_unauthenticated(test_client):
    """Requesting the profile endpoint without an authorization header returns 401."""
    response = test_client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
