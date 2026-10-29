"""
CVlect AI — Pytest Configuration & Test Fixtures
Provides isolated in-memory SQLite database sessions, FastAPI TestClient,
test users, and pre-authenticated JWT headers.
"""

import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import Base, get_db
from app.main import app
from app.models.models import User
from app.services.auth_service import hash_password, create_access_token

# In-memory SQLite for high-speed, isolated test runs
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a pristine database for each test function and drop after completion."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    """FastAPI TestClient wired to the isolated in-memory database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_candidate(test_db) -> User:
    """Create and return a standard candidate user."""
    user = User(
        email="candidate.test@example.com",
        password_hash=hash_password("CandidateSecret123!"),
        full_name="Alex River Candidate",
        role="candidate",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_recruiter(test_db) -> User:
    """Create and return a standard recruiter user."""
    user = User(
        email="recruiter.test@example.com",
        password_hash=hash_password("RecruiterSecret123!"),
        full_name="Jordan Vance Recruiter",
        role="recruiter",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers_candidate(test_user_candidate) -> dict[str, str]:
    """Generate authorization Bearer headers for the test candidate user."""
    token = create_access_token(
        data={"sub": str(test_user_candidate.id), "role": test_user_candidate.role}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_recruiter(test_user_recruiter) -> dict[str, str]:
    """Generate authorization Bearer headers for the test recruiter user."""
    token = create_access_token(
        data={"sub": str(test_user_recruiter.id), "role": test_user_recruiter.role}
    )
    return {"Authorization": f"Bearer {token}"}
