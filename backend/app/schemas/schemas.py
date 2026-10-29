"""
CVlect AI — Pydantic Schemas
Request/response validation for all API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# =============================================================================
# Auth
# =============================================================================

class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(candidate|recruiter)$")


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: int
    role: str


# =============================================================================
# Resume
# =============================================================================

class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    is_analyzed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    field: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[str] = None


class ExperienceEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[list[str]] = None


class CertificationEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[str] = None


class ProjectEntry(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[list[str]] = None
    url: Optional[str] = None


class ExtractedDataResponse(BaseModel):
    contact_info: Optional[dict] = None
    skills: Optional[list[str]] = None
    technical_skills: Optional[list[str]] = None
    soft_skills: Optional[list[str]] = None
    education: Optional[list[dict]] = None
    experience: Optional[list[dict]] = None
    certifications: Optional[list[dict]] = None
    projects: Optional[list[dict]] = None
    keywords: Optional[list[str]] = None
    domain_knowledge: Optional[list[str]] = None
    summary: Optional[str] = None
    total_experience_years: Optional[float] = 0.0
    confidence_scores: Optional[dict] = None
    missing_fields: Optional[list[str]] = None
    quality_score: Optional[float] = 0.0
    quality_suggestions: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeDetailResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    is_analyzed: bool
    created_at: datetime
    extracted_data: Optional[ExtractedDataResponse] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Jobs
# =============================================================================

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    location: Optional[str] = None
    work_mode: str = Field(default="onsite", pattern="^(remote|onsite|hybrid)$")
    experience_min: int = Field(default=0, ge=0)
    experience_max: int = Field(default=99, ge=0)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    education_requirements: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    responsibilities: Optional[list[str]] = None
    technologies: Optional[list[str]] = None
    seniority: Optional[str] = None
    category: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|closed|draft)$")


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    education_requirements: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    responsibilities: Optional[list[str]] = None
    technologies: Optional[list[str]] = None
    seniority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    recruiter_id: int
    title: str
    company: str
    description: str
    location: Optional[str] = None
    work_mode: str
    experience_min: int
    experience_max: int
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    education_requirements: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    responsibilities: Optional[list[str]] = None
    technologies: Optional[list[str]] = None
    seniority: Optional[str] = None
    category: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedJobsResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    per_page: int
    pages: int


class SavedJobResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    saved_at: datetime
    job: Optional[JobResponse] = None

    model_config = ConfigDict(from_attributes=True)



# =============================================================================
# Matching
# =============================================================================

class MatchRequest(BaseModel):
    resume_id: int
    job_id: int


class MatchScoreBreakdown(BaseModel):
    overall_score: float
    skill_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    project_score: float


class MatchExplanation(BaseModel):
    summary: Optional[str] = None
    matched_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    partially_matched: Optional[list[str]] = None
    strong_matches: Optional[list[str]] = None
    recommendations: Optional[list[str]] = None
    feature_contributions: Optional[dict] = None
    evidence: Optional[list[dict]] = None
    scoring_method: str = "weighted_feature_combination"
    is_demo_mode: bool = True


class MatchResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int
    scores: MatchScoreBreakdown
    explanation: MatchExplanation
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateMatchItem(BaseModel):
    resume_id: int
    candidate_name: str
    candidate_email: str
    overall_score: float
    skill_score: float
    experience_score: float
    matched_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    is_demo_mode: bool = True


class CandidateRankingResponse(BaseModel):
    job_id: int
    job_title: str
    candidates: list[CandidateMatchItem]
    total: int


class JobMatchItem(BaseModel):
    job_id: int
    job_title: str
    company: str
    location: Optional[str] = None
    work_mode: str
    overall_score: float
    skill_score: float
    matched_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    is_demo_mode: bool = True


class JobRecommendationResponse(BaseModel):
    resume_id: int
    jobs: list[JobMatchItem]
    total: int


# =============================================================================
# Applications
# =============================================================================

class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: int
    cover_letter: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(applied|reviewing|shortlisted|interview|offered|rejected|withdrawn)$")


class ApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    resume_id: int
    status: str
    cover_letter: Optional[str] = None
    applied_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    company: Optional[str] = None
    candidate_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Analytics
# =============================================================================

class CandidateAnalytics(BaseModel):
    total_resumes: int = 0
    analyzed_resumes: int = 0
    total_applications: int = 0
    applications_by_status: dict = {}
    avg_match_score: float = 0.0
    top_match_score: float = 0.0
    top_skills: list[str] = []
    skill_gaps: list[str] = []
    recent_activity: list[dict] = []


class RecruiterAnalytics(BaseModel):
    total_jobs: int = 0
    active_jobs: int = 0
    total_applications: int = 0
    applications_by_status: dict = {}
    avg_match_score: float = 0.0
    pipeline_stats: dict = {}
    skill_distribution: dict = {}
    recent_activity: list[dict] = []


class FairnessReport(BaseModel):
    report_type: str
    metrics: dict = {}
    limitations: list[str] = []
    sample_size: int = 0
    generated_at: datetime
    is_diagnostic: bool = True  # always diagnostic, never proof of fairness


# =============================================================================
# AI Assistant
# =============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[dict] = None  # {resume_id, job_id, ...}


class ChatResponse(BaseModel):
    response: str
    sources: Optional[list[dict]] = None
    is_llm_generated: bool = True


# =============================================================================
# Pagination
# =============================================================================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
