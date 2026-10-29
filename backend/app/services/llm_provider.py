"""
CVlect AI — NVIDIA NIM LLM Provider
Integrates NVIDIA NIM microservices via the OpenAI-compatible API client.
Handles graceful fallback when API credentials are not configured.
"""

from typing import Optional, Any
import json
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)


class LLMProvider:
    """
    Wrapper for NVIDIA NIM API using OpenAI client.
    Never exposes API keys in logs or exceptions.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.nvidia_api_key
        self.base_url = base_url or settings.nvidia_base_url
        self.model = model or settings.nvidia_model
        self._client: Optional[Any] = None

        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
                logger.info(f"Initialized NVIDIA NIM client with model '{self.model}'")
            except ImportError:
                logger.warning("OpenAI client library is not installed. LLMProvider unavailable.")
                self._client = None
            except Exception as e:
                logger.warning(f"Could not initialize NVIDIA NIM client: {e}")
                self._client = None
        else:
            logger.info("NVIDIA NIM API key is not configured. Operating in fallback mode.")

    @property
    def is_available(self) -> bool:
        """Check if LLM service is configured and ready."""
        return self._client is not None and bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Optional[str]:
        """
        Execute completion request against NVIDIA NIM endpoint.
        Returns text response or None if unavailable/error.
        """
        if not self.is_available:
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception as e:
            logger.error(f"NVIDIA NIM completion error: {type(e).__name__} - {e}")
            return None

    def generate_resume_summary(self, parsed_resume: dict[str, Any]) -> Optional[str]:
        """Generate a concise professional candidate summary from structured parsed data."""
        if not self.is_available:
            return None

        # Prepare safe context summary (exclude raw personally identifiable info)
        skills = parsed_resume.get("skills", [])[:15]
        years = parsed_resume.get("total_experience_years", 0.0)
        education = [e.get("degree") for e in parsed_resume.get("education", []) if e.get("degree")]
        roles = [exp.get("title") for exp in parsed_resume.get("experience", []) if exp.get("title")]

        prompt = (
            f"Generate a professional, objective 2-3 sentence executive summary for a candidate with the following credentials:\n"
            f"- Verified Experience: {years} years\n"
            f"- Recent Roles: {', '.join(roles[:3]) if roles else 'Software Professional'}\n"
            f"- Key Skills: {', '.join(skills)}\n"
            f"- Education: {', '.join(education) if education else 'Technical background'}\n"
            f"Focus strictly on competencies, experience level, and core technical strengths without hype or exaggeration."
        )

        system_prompt = "You are an expert technical talent scout providing concise, factual resume summaries."
        return self.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=256, temperature=0.2)

    def generate_match_explanation(self, match_data: dict[str, Any]) -> Optional[str]:
        """Generate an AI narrative assessing candidate alignment with job requirements."""
        if not self.is_available:
            return None

        overall = match_data.get("overall_score", 0.0)
        matched = match_data.get("matched_skills", [])[:6]
        missing = match_data.get("missing_skills", [])[:4]
        job_title = match_data.get("job_title", "the role")
        company = match_data.get("company", "the hiring team")

        prompt = (
            f"Write a concise 3-sentence recruiter assessment for a candidate matching for '{job_title}' at '{company}':\n"
            f"- Match Score: {overall}%\n"
            f"- Strong Skill Matches: {', '.join(matched) if matched else 'None'}\n"
            f"- Missing Core Skills: {', '.join(missing) if missing else 'None'}\n"
            f"Explain why this match score was determined and advise the recruiter on candidate suitability."
        )

        system_prompt = "You are a senior recruitment advisor explaining AI match analytics transparently."
        return self.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=256, temperature=0.3)

    def generate_skill_recommendations(
        self,
        resume_skills: list[str],
        job_skills: list[str],
    ) -> list[str]:
        """
        Produce actionable skill suggestions to bridge gaps for target roles.
        Falls back to set difference if LLM is unavailable.
        """
        missing_rule_based = [s for s in job_skills if s.lower() not in [r.lower() for r in resume_skills]]

        if not self.is_available:
            return missing_rule_based[:5]

        prompt = (
            f"Candidate has current skills: {', '.join(resume_skills[:15])}\n"
            f"Target position seeks: {', '.join(job_skills[:15])}\n"
            f"Identify 4-5 high-priority skills or technologies the candidate should acquire to become competitive. "
            f"Return ONLY a valid JSON list of strings, e.g. [\"Docker\", \"Kubernetes\"]."
        )

        system_prompt = "You are a career coaching engine. Output exclusively valid JSON arrays."
        response = self.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=150, temperature=0.1)

        if response:
            try:
                # Find JSON brackets
                start = response.find("[")
                end = response.rfind("]") + 1
                if start != -1 and end != -1:
                    parsed = json.loads(response[start:end])
                    if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                        return parsed[:6]
            except Exception as e:
                logger.debug(f"Failed to parse LLM skill recommendations JSON: {e}")

        return missing_rule_based[:5]


# Global singleton LLM provider instance
llm_provider = LLMProvider()
