"""
CVlect AI — Conversational Assistant Service
RAG-enabled AI copilot for candidates and recruiters.
Enforces strict role-based data isolation and grounding.
"""

from typing import Optional, Any
from sqlalchemy.orm import Session

from app.models.models import Resume, Job, Application, MatchResult, ExtractedResumeData
from app.schemas.schemas import ChatResponse
from app.services.llm_provider import llm_provider, LLMProvider
from app.utils import get_logger

logger = get_logger(__name__)


class AssistantService:
    """Conversational assistant service incorporating retrieval-augmented generation."""
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or llm_provider

    def chat(
        self,
        user_id: int,
        role: str,
        message: str,
        context: Optional[dict[str, Any]],
        db: Session,
    ) -> ChatResponse:
        """
        Process chat query with contextual retrieval while strictly enforcing role isolation.
        """
        if not self.provider.is_available:
            return ChatResponse(
                response=(
                    "The AI Assistant is currently in standby mode because the NVIDIA NIM API key "
                    "is not configured in the environment. To activate conversational assistance, "
                    "please set NVIDIA_API_KEY in your environment or .env file.\n\n"
                    "All core platform capabilities (resume parsing, skill extraction, deterministic "
                    "matching, and neural ranking) remain fully operational."
                ),
                sources=[],
                is_llm_generated=False,
            )

        context = context or {}
        retrieved_context_texts: list[str] = []
        sources: list[dict[str, Any]] = []

        # 1. Context Retrieval based on Role & Permissions
        resume_id = context.get("resume_id")
        job_id = context.get("job_id")

        if role == "candidate":
            # Candidate context retrieval
            if resume_id:
                resume = (
                    db.query(Resume)
                    .filter(Resume.id == resume_id, Resume.user_id == user_id)
                    .first()
                )
                if resume and resume.extracted_data:
                    ed = resume.extracted_data
                    retrieved_context_texts.append(
                        f"Candidate Resume Details:\n"
                        f"- Total Experience: {ed.total_experience_years} years\n"
                        f"- Extracted Skills: {', '.join((ed.skills or [])[:20])}\n"
                        f"- Education: {ed.education}\n"
                        f"- Quality Score: {ed.quality_score}/100"
                    )
                    sources.append({"type": "resume", "id": resume.id, "title": resume.filename})

            if job_id:
                job = db.query(Job).filter(Job.id == job_id, Job.status == "active").first()
                if job:
                    retrieved_context_texts.append(
                        f"Target Job Opportunity:\n"
                        f"- Title: {job.title} at {job.company}\n"
                        f"- Required Skills: {', '.join(job.required_skills or [])}\n"
                        f"- Experience Required: {job.experience_min} to {job.experience_max} years\n"
                        f"- Work Mode: {job.work_mode}"
                    )
                    sources.append({"type": "job", "id": job.id, "title": f"{job.title} ({job.company})"})

            # Also check if match result exists
            if resume_id and job_id:
                match = (
                    db.query(MatchResult)
                    .filter(MatchResult.resume_id == resume_id, MatchResult.job_id == job_id)
                    .first()
                )
                if match:
                    retrieved_context_texts.append(
                        f"Match Evaluation:\n"
                        f"- Overall Score: {match.overall_score}%\n"
                        f"- Matched Skills: {', '.join(match.matched_skills or [])}\n"
                        f"- Missing Skills: {', '.join(match.missing_skills or [])}\n"
                        f"- Recommendations: {', '.join(match.recommendations or [])}"
                    )
                    sources.append({"type": "match_result", "id": match.id, "title": "Match Breakdown"})

        elif role == "recruiter":
            # Recruiter context retrieval
            if job_id:
                job = db.query(Job).filter(Job.id == job_id, Job.recruiter_id == user_id).first()
                if job:
                    retrieved_context_texts.append(
                        f"Your Job Posting:\n"
                        f"- Title: {job.title} ({job.status})\n"
                        f"- Required Skills: {', '.join(job.required_skills or [])}\n"
                        f"- Preferred Skills: {', '.join(job.preferred_skills or [])}\n"
                        f"- Total Applications: {len(job.applications)}"
                    )
                    sources.append({"type": "job", "id": job.id, "title": job.title})

            if resume_id:
                # Recruiter can only inspect resume if candidate applied to one of recruiter's jobs
                application = (
                    db.query(Application)
                    .join(Job, Application.job_id == Job.id)
                    .filter(Application.resume_id == resume_id, Job.recruiter_id == user_id)
                    .first()
                )
                if application and application.resume and application.resume.extracted_data:
                    ed = application.resume.extracted_data
                    retrieved_context_texts.append(
                        f"Applicant Resume Summary:\n"
                        f"- Experience: {ed.total_experience_years} years\n"
                        f"- Skills: {', '.join((ed.skills or [])[:15])}\n"
                        f"- Recent Roles: {[e.get('title') for e in (ed.experience or [])[:2]]}"
                    )
                    sources.append({"type": "resume", "id": resume_id, "title": "Applicant Profile"})

        # 2. Build Prompt
        system_prompt = (
            "You are CVlect AI, an intelligent talent and recruitment copilot. "
            "You provide concise, factual, and actionable assistance to users. "
            "Never fabricate candidate credentials or job requirements beyond the provided context. "
            "Ensure privacy and professional tone at all times."
        )

        context_block = "\n\n".join(retrieved_context_texts) if retrieved_context_texts else "No specific documents loaded."

        user_prompt = (
            f"User Role: {role.capitalize()}\n"
            f"Context Data:\n{context_block}\n\n"
            f"User Question: {message}\n\n"
            f"Please provide a helpful, tailored, and structured response:"
        )

        llm_response = self.provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=600,
            temperature=0.3,
        )

        if not llm_response:
            return ChatResponse(
                response="I received your request, but could not complete generation at this time. Please try again shortly.",
                sources=sources,
                is_llm_generated=False,
            )

        return ChatResponse(
            response=llm_response,
            sources=sources,
            is_llm_generated=True,
        )


# Global singleton assistant service instance
assistant_service = AssistantService()
