import re
from typing import Any, Dict, List


class RecommendationEngine:
    def __init__(self) -> None:
        # Predefined mappings for skill gaps to courses & certifications
        self.recommendations_db = {
            "fastapi": {
                "courses": ["FastAPI Fundamentals (Udemy)", "Complete APIs with FastAPI and Python"],
                "certifications": ["AWS Certified Developer - Associate (to host APIs)"]
            },
            "python": {
                "courses": ["Python for Data Science and Machine Learning", "Complete Python Bootcamp (Udemy)"],
                "certifications": ["PCEP – Certified Entry-Level Python Programmer"]
            },
            "machine learning": {
                "courses": ["Machine Learning Specialization by Andrew Ng", "Applied Machine Learning Course"],
                "certifications": ["AWS Certified Machine Learning - Specialty", "Google Professional ML Engineer"]
            },
            "pytorch": {
                "courses": ["PyTorch for Deep Learning Bootcamp", "Deep Learning with PyTorch (Coursera)"],
                "certifications": ["NVIDIA Deep Learning Institute Certificate"]
            },
            "tensorflow": {
                "courses": ["TensorFlow Developer Professional Certificate", "DeepLearning.AI TensorFlow Developer"],
                "certifications": ["TensorFlow Developer Certificate"]
            },
            "aws": {
                "courses": ["AWS Cloud Practitioner Essentials", "Ultimate AWS Certified Solutions Architect"],
                "certifications": ["AWS Certified Cloud Practitioner", "AWS Certified Solutions Architect - Associate"]
            },
            "docker": {
                "courses": ["Docker for Developers (Udemy)", "Docker & Kubernetes: The Practical Guide"],
                "certifications": ["Docker Certified Associate (DCA)"]
            },
            "kubernetes": {
                "courses": ["Certified Kubernetes Administrator (CKA) BootCamp", "Kubernetes for DevOps"],
                "certifications": ["Certified Kubernetes Administrator (CKA)", "Certified Kubernetes Application Developer (CKAD)"]
            },
            "react": {
                "courses": ["React - The Complete Guide (Academind)", "Modern React with Redux"],
                "certifications": ["Meta Front-End Developer Professional Certificate"]
            },
            "typescript": {
                "courses": ["Understanding TypeScript (Udemy)", "TypeScript Design Patterns"],
                "certifications": ["Microsoft Certified: HTML5 with JavaScript and CSS3"]
            },
            "sql": {
                "courses": ["The Complete SQL Bootcamp (Udemy)", "PostgreSQL for Developers"],
                "certifications": ["Oracle Database SQL Certified Associate"]
            }
        }

    def recommend(self, ranked_candidates: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        recommendations = []
        for candidate in ranked_candidates[:limit]:
            job_description = candidate.get("job_description", "")
            parsed = candidate.get("parsed_resume", {})
            resume_skills = {str(skill).strip().lower() for skill in parsed.get("skills", []) if str(skill).strip()}

            # Parse skills from job description
            job_tokens = self._extract_skills_from_text(job_description.lower())
            
            # Find missing skills
            missing_skills = sorted(list(job_tokens - resume_skills))

            # Resolve courses and certifications dynamically
            courses = []
            certifications = []
            
            for skill in missing_skills:
                if skill in self.recommendations_db:
                    db_entry = self.recommendations_db[skill]
                    courses.extend(db_entry["courses"])
                    certifications.extend(db_entry["certifications"])
            
            # Deduplicate and cap
            courses = list(dict.fromkeys(courses))[:3]
            certifications = list(dict.fromkeys(certifications))[:3]

            # Add default suggestions if empty
            if not courses:
                courses = ["System Design & Microservices Architecture", "Advanced Software Engineering Principles"]
            if not certifications:
                certifications = ["AWS Certified Cloud Practitioner"]

            # General improvements
            resume_improvements = [
                "Quantify achievements: Use metrics like 'Reduced latency by 30%' instead of just listing responsibilities.",
                "Tailor summary: Make sure your profile header mirrors the job title (e.g. 'Senior Frontend Engineer')."
            ]
            if missing_skills:
                resume_improvements.append(f"Add a technical project demonstrating hands-on experience with: {', '.join(missing_skills[:2]).upper()}.")

            # Career paths based on present/missing skills
            career_suggestions = []
            if "react" in resume_skills or "html" in resume_skills:
                career_suggestions.append("Prepare for Senior Full Stack or Frontend Architect roles.")
            if "machine learning" in resume_skills or "python" in resume_skills:
                career_suggestions.append("Explore Applied Machine Learning & MLOps Career Paths.")
            else:
                career_suggestions.append("Target Backend Software Engineer roles in Cloud computing.")

            recommendations.append({
                **candidate,
                "recommendations": {
                    "missing_skills": [s.upper() for s in missing_skills[:5]],
                    "courses": courses,
                    "certifications": certifications,
                    "resume_improvements": resume_improvements,
                    "career_suggestions": career_suggestions,
                },
            })
        return recommendations

    def _extract_skills_from_text(self, text: str) -> set:
        # Simple extraction logic matching common tech terms
        skills = {
            "python", "javascript", "typescript", "c++", "java", "sql", "postgresql", 
            "react", "fastapi", "django", "aws", "azure", "docker", "kubernetes", "machine learning",
            "pytorch", "tensorflow", "xgboost"
        }
        found = set()
        text_lower = text.lower()
        for s in skills:
            pattern = rf"\b{re.escape(s)}\b"
            if s in {"c++"}:
                pattern = rf"\b{re.escape(s)}"
            if re.search(pattern, text_lower):
                found.add(s)
        return found
