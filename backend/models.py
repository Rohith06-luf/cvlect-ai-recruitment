"""
Pydantic models for request/response validation in the CVlect FastAPI backend.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = Field(..., pattern="^(recruiter|candidate)$")
    phone: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    team: Optional[str] = None
    about: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    avatar_initials: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    team: Optional[str] = None
    about: Optional[str] = None
    verified: bool = False
    created_at: Optional[str] = None


class TokenOut(BaseModel):
    token: str
    user: UserOut


# ---------- Jobs ----------
class JobCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None


class JobOut(BaseModel):
    id: int
    recruiter_id: int
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    status: str = "open"
    created_at: Optional[str] = None


# ---------- Candidate Profile ----------
class CandidateProfileOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    role: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[str] = None
    summary: Optional[str] = None
    resume_path: Optional[str] = None
    resume_score: int = 0
    ats_score: int = 0
    keywords_score: int = 0
    experience_match: int = 0
    projects_score: int = 0
    education_score: int = 0
    achievements_score: int = 0
    career_health: int = 0
    current_skills: List[str] = []
    missing_skills: List[str] = []
    created_at: Optional[str] = None


# ---------- Applications ----------
class ApplicationCreate(BaseModel):
    job_id: int


class ApplicationOut(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: str
    applied_date: str
    # joined job fields
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None


# ---------- Pipeline ----------
class PipelineEntryOut(BaseModel):
    id: int
    recruiter_id: int
    job_id: int
    candidate_id: int
    profile_id: Optional[int] = None
    score: int
    rank: int
    top_match: bool = False
    reason: Optional[str] = None
    status: str = "pending"
    created_at: Optional[str] = None
    # joined candidate fields
    name: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[str] = None
    summary: Optional[str] = None
    matched: List[str] = []
    missing: List[str] = []


class PipelineStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|shortlisted|selected|rejected)$")


# ---------- Activities ----------
class ActivityOut(BaseModel):
    id: int
    recruiter_id: int
    text: str
    created_at: str


# ---------- Stats ----------
class StatsOut(BaseModel):
    total_resumes: int
    shortlisted: int
    selected: int
    rejected: int


# ---------- Generic ----------
class MessageOut(BaseModel):
    message: str


class IdOut(BaseModel):
    id: int
