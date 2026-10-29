"""
CVlect AI — SQLAlchemy ORM Models
All database tables for the recruitment platform.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, LargeBinary, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# =============================================================================
# User & Profiles
# =============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)          # "candidate" | "recruiter"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate")
    saved_jobs = relationship("SavedJob", back_populates="candidate", cascade="all, delete-orphan")
    analysis_history = relationship("AnalysisHistory", back_populates="user")
    audit_events = relationship("AuditEvent", back_populates="user")


# =============================================================================
# Resume & Extracted Data
# =============================================================================

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)     # "pdf" | "docx"
    file_size = Column(Integer, nullable=False)         # bytes
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="resumes")
    extracted_data = relationship(
        "ExtractedResumeData", back_populates="resume",
        uselist=False, cascade="all, delete-orphan",
    )
    applications = relationship("Application", back_populates="resume")
    match_results = relationship("MatchResult", back_populates="resume", cascade="all, delete-orphan")


class ExtractedResumeData(Base):
    __tablename__ = "extracted_resume_data"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), unique=True, nullable=False)

    # Raw text
    raw_text = Column(Text)

    # Structured fields (all stored as JSON for flexibility)
    contact_info = Column(JSON)       # {name, email, phone, location, linkedin, github}
    skills = Column(JSON)             # ["python", "react", ...]
    technical_skills = Column(JSON)   # ["python", "pytorch", ...]
    soft_skills = Column(JSON)        # ["leadership", "communication", ...]
    education = Column(JSON)          # [{degree, institution, year, gpa, field}, ...]
    experience = Column(JSON)         # [{title, company, start_date, end_date, description, technologies}, ...]
    certifications = Column(JSON)     # [{name, issuer, year, url}, ...]
    projects = Column(JSON)           # [{name, description, technologies, url}, ...]
    keywords = Column(JSON)           # ["machine learning", "api design", ...]
    domain_knowledge = Column(JSON)   # ["fintech", "healthcare", ...]

    # AI-generated fields (clearly distinguished from extracted facts)
    summary = Column(Text)                        # AI-generated resume summary
    total_experience_years = Column(Float, default=0.0)

    # Quality & confidence
    confidence_scores = Column(JSON)  # {skills: 0.9, education: 0.85, ...}
    missing_fields = Column(JSON)     # ["certifications", "projects"]
    quality_score = Column(Float, default=0.0)
    quality_suggestions = Column(JSON)  # ["Add more project details", ...]

    # Embedding vector (stored as pickled numpy bytes)
    embedding = Column(LargeBinary)

    created_at = Column(DateTime, default=_utcnow)

    resume = relationship("Resume", back_populates="extracted_data")


# =============================================================================
# Jobs
# =============================================================================

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255))
    work_mode = Column(String(20), default="onsite")   # remote | onsite | hybrid
    experience_min = Column(Integer, default=0)
    experience_max = Column(Integer, default=99)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)

    # Structured requirements (JSON arrays)
    required_skills = Column(JSON)
    preferred_skills = Column(JSON)
    education_requirements = Column(JSON)
    certifications = Column(JSON)
    responsibilities = Column(JSON)
    technologies = Column(JSON)

    seniority = Column(String(50))                      # junior | mid | senior | lead | principal
    category = Column(String(100))                      # engineering | data-science | design | ...
    status = Column(String(20), default="active")       # active | closed | draft

    # Embedding vector
    embedding = Column(LargeBinary)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    recruiter = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")
    saved_by = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")


# =============================================================================
# Applications
# =============================================================================

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),
    )

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    status = Column(String(20), default="applied")
    # applied | reviewing | shortlisted | interview | offered | rejected | withdrawn
    cover_letter = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")


# =============================================================================
# Match Results
# =============================================================================

class MatchResult(Base):
    __tablename__ = "match_results"
    __table_args__ = (
        UniqueConstraint("resume_id", "job_id", name="uq_resume_job_match"),
        Index("ix_match_overall_score", "overall_score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)

    # Scores (0–100 scale)
    overall_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    project_score = Column(Float, default=0.0)

    # Feature vector & explanation
    feature_vector = Column(JSON)
    explanation = Column(JSON)             # structured explanation object
    matched_skills = Column(JSON)
    missing_skills = Column(JSON)
    partially_matched = Column(JSON)
    strong_matches = Column(JSON)
    recommendations = Column(JSON)         # skill-gap / improvement suggestions

    # Transparency flag
    is_demo_mode = Column(Boolean, default=True)

    created_at = Column(DateTime, default=_utcnow)

    resume = relationship("Resume", back_populates="match_results")
    job = relationship("Job", back_populates="match_results")


# =============================================================================
# Saved Jobs (Bookmarks)
# =============================================================================

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_saved_candidate_job"),
    )

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    saved_at = Column(DateTime, default=_utcnow)

    candidate = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by")


# =============================================================================
# Analysis History & Audit
# =============================================================================

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="analysis_history")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="audit_events")
