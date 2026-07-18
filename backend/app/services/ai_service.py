import re
from pathlib import Path
from typing import Any, List, Dict, Tuple

from app.ai.bias_detection.bias_detector import BiasDetector
from app.ai.embeddings.embedder import EmbeddingEngine
from app.ai.explainability.shap_explainer import SHAPExplainer
from app.ai.fraud_detection.fraud_detector import FraudDetector
from app.ai.parser.resume_parser import ResumeParser
from app.ai.ranking.xgboost_ranker import XGBoostRanker
from app.ai.recommendation.recommender import RecommendationEngine
from app.ai.semantic_match.matcher import SemanticMatcher
from app.ai.summarizer.resume_summarizer import ResumeSummarizer
from app.ai.vector_db.faiss_store import FAISSStore


class AIService:
    def __init__(self) -> None:
        self.parser = ResumeParser()
        self.embedder = EmbeddingEngine()
        self.matcher = SemanticMatcher(self.embedder)
        self.ranker = XGBoostRanker()
        self.explainer = SHAPExplainer()
        self.fraud_detector = FraudDetector()
        self.bias_detector = BiasDetector()
        self.recommender = RecommendationEngine()
        self.summarizer = ResumeSummarizer()
        self.store = FAISSStore()

    def _calculate_metrics(self, parsed: dict, text: str, job_description: str) -> dict:
        if not job_description:
            # Default fallback when no job description is provided
            skill_match = 0.5
            exp_match = 0.5
            edu_match = 0.5
            keyword_match = 0.5
            semantic_sim = 0.5
            final_score = 65
            return {
                "skill_match": skill_match,
                "experience_match": exp_match,
                "education_match": edu_match,
                "keyword_match": keyword_match,
                "semantic_similarity": semantic_sim,
                "final_score": final_score
            }

        # 1. Skill Match
        resume_skills = {s.lower().strip() for s in parsed.get("skills", []) if s.strip()}
        required_skills = self.recommender._extract_skills_from_text(job_description)
        if required_skills:
            skill_overlap = resume_skills & required_skills
            skill_match = len(skill_overlap) / len(required_skills)
        else:
            skill_match = self._compute_skill_overlap(parsed, job_description)

        # 2. Experience Match
        candidate_exp = parsed.get("experience_years", 0)
        # Extract required years from job description (e.g., "5+ years", "3 years")
        exp_req_matches = re.findall(r"(\d+)\s*(?:\+?\s*years?|yrs?)", job_description, re.IGNORECASE)
        required_exp = int(exp_req_matches[0]) if exp_req_matches else 2
        if required_exp > 0:
            exp_match = min(1.0, candidate_exp / required_exp)
        else:
            exp_match = 1.0

        # 3. Education Match
        edu_match = 0.1
        edu_lower = [e.lower() for e in parsed.get("education", [])]
        jd_lower = job_description.lower()
        if any(deg in jd_lower for deg in ["phd", "ph.d", "doctor"]):
            if any(deg in edu_lower for deg in ["phd", "ph.d", "doctor"]):
                edu_match = 1.0
            elif any(deg in edu_lower for deg in ["m.tech", "master", "m.sc", "msc", "m.s", "m.e", "mba"]):
                edu_match = 0.7
            else:
                edu_match = 0.4
        elif any(deg in jd_lower for deg in ["m.tech", "master", "m.sc", "msc", "m.s", "m.e", "mba"]):
            if any(deg in edu_lower for deg in ["phd", "ph.d", "doctor"]):
                edu_match = 1.0
            elif any(deg in edu_lower for deg in ["m.tech", "master", "m.sc", "msc", "m.s", "m.e", "mba"]):
                edu_match = 1.0
            elif any(deg in edu_lower for deg in ["b.tech", "b.e", "bachelor", "b.sc", "bsc"]):
                edu_match = 0.6
            else:
                edu_match = 0.3
        else:
            if any(deg in edu_lower for deg in ["phd", "ph.d", "doctor"]):
                edu_match = 1.0
            elif any(deg in edu_lower for deg in ["m.tech", "master", "m.sc", "msc", "m.s", "m.e", "mba"]):
                edu_match = 0.8
            elif any(deg in edu_lower for deg in ["b.tech", "b.e", "bachelor", "b.sc", "bsc"]):
                edu_match = 0.6
            elif edu_lower:
                edu_match = 0.4

        # 4. Keyword Match
        job_words = {w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", job_description) if w.lower() not in {
            "the", "and", "with", "for", "are", "you", "will", "have", "this", "that", "from"
        }}
        resume_words = {w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)}
        if job_words:
            keyword_match = len(resume_words & job_words) / len(job_words)
        else:
            keyword_match = 0.5

        # 5. Semantic Similarity
        try:
            semantic_sim = self.matcher.match(text, job_description)
        except Exception:
            semantic_sim = 0.5

        # Weighted calculation
        final_score = int(round(
            (skill_match * 0.35 +
             exp_match * 0.20 +
             edu_match * 0.15 +
             keyword_match * 0.15 +
             semantic_sim * 0.15) * 100
        ))
        
        # Ensure it's between 0 and 100
        final_score = max(0, min(100, final_score))

        return {
            "skill_match": skill_match,
            "experience_match": exp_match,
            "education_match": edu_match,
            "keyword_match": keyword_match,
            "semantic_similarity": semantic_sim,
            "final_score": final_score
        }

    def process_resume(self, file_path: str, job_description: str | None = None) -> Dict[str, Any]:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # 1. Text extraction and NER parsing
        text = self.parser.extract_text_from_pdf(file_path)
        parsed = self.parser.parse(text)
        skills = parsed.get("skills", [])
        experience = parsed.get("experience_years", 0)

        # Calculate metrics using job description
        metrics = self._calculate_metrics(parsed, text, job_description or "")
        ats_score = metrics["final_score"]
        match_percentage = metrics["final_score"]

        projects_score = min(1.0, len(parsed.get("projects", [])) * 0.25)
        certs_score = min(1.0, len(parsed.get("certifications", [])) * 0.2)

        candidate = {
            "parsed_resume": parsed,
            "raw_text": text,
            "job_description": job_description or "",
            "features": {
                "semantic_similarity": round(metrics["semantic_similarity"], 4),
                "experience_years": experience,
                "education_score": round(metrics["education_match"], 4),
                "skill_overlap": round(metrics["skill_match"], 4),
                "projects_score": projects_score,
                "certifications_score": certs_score,
                "keyword_match": round(metrics["keyword_match"], 4),
            },
        }
        
        # 5. Enrich candidate with explainability, fraud, bias, and summary reports
        candidate = self._enrich_candidate(candidate)

        return {
            "text": text,
            "parsed": parsed,
            "ats_score": ats_score,
            "match_percentage": match_percentage,
            "skills": skills,
            "summary": candidate.get("summary", {}),
            "explanation": candidate.get("explanation"),
            "fraud_report": candidate.get("fraud_report"),
            "bias_report": candidate.get("bias_report"),
            "features": candidate.get("features"),
        }

    def rank_candidates(self, candidates: List[Dict[str, Any]], job_description: str) -> List[Dict[str, Any]]:
        # First score and enrich every candidate
        enriched = []
        for candidate in candidates:
            resume_text = candidate.get("resume_text") or candidate.get("raw_text") or ""
            if not resume_text:
                continue
            scored = self.score_candidate(resume_text, job_description, candidate_payload=candidate)
            enriched.append(scored)

        # ranker.rank() expects a list of dicts each with a "features" key
        ranked = self.ranker.rank(enriched)

        # Assign ordinal ranks
        for rank_idx, cand in enumerate(ranked):
            cand["rank"] = rank_idx + 1
            cand["top_match"] = rank_idx == 0 and cand.get("rank_score", 0.0) >= 0.75

        return ranked

    def score_candidate(self, resume_text: str, job_description: str, candidate_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        parsed = self.parser.parse(resume_text)
        
        # Calculate metrics using job description
        metrics = self._calculate_metrics(parsed, resume_text, job_description)
        
        projects_score = min(1.0, len(parsed.get("projects", [])) * 0.25)
        certs_score = min(1.0, len(parsed.get("certifications", [])) * 0.2)

        features = {
            "semantic_similarity": round(metrics["semantic_similarity"], 4),
            "experience_years": parsed.get("experience_years", 0),
            "education_score": round(metrics["education_match"], 4),
            "skill_overlap": round(metrics["skill_match"], 4),
            "projects_score": projects_score,
            "certifications_score": certs_score,
            "keyword_match": round(metrics["keyword_match"], 4),
        }
        
        candidate = {
            "parsed_resume": parsed, 
            "raw_text": resume_text, 
            "features": features, 
            "job_description": job_description,
            "match_percentage": metrics["final_score"],
            "ats_score": metrics["final_score"],
            "rank_score": metrics["final_score"] / 100.0,
        }
        
        if candidate_payload:
            candidate.update(candidate_payload)
            
        return self._enrich_candidate(candidate)

    def explain_candidate(self, candidate: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        return self.explainer.explain(candidate, job_description)

    def detect_fraud(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        return self.fraud_detector.detect(candidate)

    def analyze_bias(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        return self.bias_detector.analyze(candidate)

    def recommend(self, ranked_candidates: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        return self.recommender.recommend(ranked_candidates, limit=limit)

    def summarize(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        return self.summarizer.summarize(candidate)

    def add_to_vector_store(self, candidate: Dict[str, Any]) -> None:
        text = candidate.get("raw_text") or ""
        if not text:
            return
        vector = self.embedder.embed_text(text)
        
        metadata = {
            "profile_id": candidate.get("id") or candidate.get("candidate_id") or "cand_uuid",
            "name": candidate.get("parsed_resume", {}).get("name", "Candidate"),
            "skills": candidate.get("parsed_resume", {}).get("skills", []),
            "experience": f"{candidate.get('parsed_resume', {}).get('experience_years', 0)} years",
            "summary": candidate.get("summary", {}).get("summary", ""),
        }
        self.store.add(vector, metadata)

    def search_vector_store(self, query: str, top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        vector = self.embedder.embed_text(query)
        return self.store.search(vector, top_k=top_k)

    def _enrich_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        candidate["summary"] = self.summarize(candidate)
        candidate["fraud_report"] = self.detect_fraud(candidate)
        candidate["bias_report"] = self.bias_detector.analyze(candidate)
        candidate["explanation"] = self.explain_candidate(candidate, candidate.get("job_description", ""))
        self.add_to_vector_store(candidate)
        return candidate

    def _compute_skill_overlap(self, parsed: Dict[str, Any], job_description: str) -> float:
        resume_skills = {str(skill).strip().lower() for skill in parsed.get("skills", []) if str(skill).strip()}
        if not resume_skills:
            return 0.0

        # Regex extract skills out of the job description
        job_tokens = {
            token.lower()
            for token in re.findall(r"\b[a-zA-Z0-9+#.-]+\b", job_description.lower())
            if len(token) > 2 and token.lower() not in {
                "the", "and", "with", "for", "are", "we", "you", "will", "have", 
                "strong", "experience", "backend", "engineer", "developer", "required"
            }
        }
        if not job_tokens:
            return 0.0

        # Compute intersection
        overlap = resume_skills & job_tokens
        return round(len(overlap) / max(1, len(job_tokens)), 4)
