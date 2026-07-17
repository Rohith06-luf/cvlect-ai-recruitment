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

    def process_resume(self, file_path: str, job_description: str | None = None) -> Dict[str, Any]:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # 1. Text extraction and NER parsing
        text = self.parser.extract_text_from_pdf(file_path)
        parsed = self.parser.parse(text)
        skills = parsed.get("skills", [])
        experience = parsed.get("experience_years", 0)

        # 2. Semantic Similarity Score (Sentence-BERT cosine similarity)
        semantic_similarity = 0.0
        if job_description:
            semantic_similarity = self.matcher.match(text, job_description)

        # 3. Features matrix calculations
        skill_overlap = self._compute_skill_overlap(parsed, job_description or "")
        
        # Education rating
        edu_score = 0.1
        edu_lower = [e.lower() for e in parsed.get("education", [])]
        if any(deg in edu_lower for deg in ["phd", "ph.d", "doctor"]):
            edu_score = 1.0
        elif any(deg in edu_lower for deg in ["m.tech", "master", "m.sc", "msc", "m.s", "m.e", "mba"]):
            edu_score = 0.8
        elif any(deg in edu_lower for deg in ["b.tech", "b.e", "bachelor", "b.sc", "bsc"]):
            edu_score = 0.6
        elif edu_lower:
            edu_score = 0.4
            
        projects_score = min(1.0, len(parsed.get("projects", [])) * 0.25)
        certs_score = min(1.0, len(parsed.get("certifications", [])) * 0.2)

        # 4. Standard ATS scoring logic
        ats_score = min(100, int(55 + min(20, len(skills) * 2) + min(15, experience * 2) + int(edu_score * 10)))
        match_percentage = min(100, int(ats_score * 0.7 + (semantic_similarity * 100) * 0.15 + (skill_overlap * 100) * 0.15))

        candidate = {
            "parsed_resume": parsed,
            "raw_text": text,
            "job_description": job_description or "",
            "features": {
                "semantic_similarity": round(semantic_similarity, 4),
                "experience_years": experience,
                "education_score": edu_score,
                "skill_overlap": round(skill_overlap, 4),
                "projects_score": projects_score,
                "certifications_score": certs_score,
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
        semantic_similarity = self.matcher.match(resume_text, job_description)
        
        skill_overlap = self._compute_skill_overlap(parsed, job_description)
        
        edu_score = 0.1
        edu_lower = [e.lower() for e in parsed.get("education", [])]
        if any(deg in edu_lower for deg in ["phd", "ph.d", "doctor"]):
            edu_score = 1.0
        elif any(deg in edu_lower for deg in ["m.tech", "master", "m.sc", "msc", "m.s", "m.e", "mba"]):
            edu_score = 0.8
        elif any(deg in edu_lower for deg in ["b.tech", "b.e", "bachelor", "b.sc", "bsc"]):
            edu_score = 0.6
        elif edu_lower:
            edu_score = 0.4
            
        projects_score = min(1.0, len(parsed.get("projects", [])) * 0.25)
        certs_score = min(1.0, len(parsed.get("certifications", [])) * 0.2)

        features = {
            "semantic_similarity": round(semantic_similarity, 4),
            "experience_years": parsed.get("experience_years", 0),
            "education_score": edu_score,
            "skill_overlap": round(skill_overlap, 4),
            "projects_score": projects_score,
            "certifications_score": certs_score,
        }
        
        candidate = {
            "parsed_resume": parsed, 
            "raw_text": resume_text, 
            "features": features, 
            "job_description": job_description
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
