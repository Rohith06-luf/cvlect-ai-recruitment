"""
verify_ai.py  –  End-to-end smoke test for the AI/ML layer.
Run from the backend/ directory with the venv active:
    python verify_ai.py
"""
import sys, textwrap

PASS = "✅"
FAIL = "❌"
results = []

SAMPLE_RESUME = textwrap.dedent("""
    John Doe
    Senior Python Engineer
    Email: john.doe@email.com  |  Phone: +1-555-0100

    SUMMARY
    Results-driven software engineer with 5 years of experience building scalable APIs
    and data pipelines. Passionate about clean code and machine learning.

    SKILLS
    Python, FastAPI, Docker, PostgreSQL, Redis, scikit-learn, TensorFlow, AWS, Git

    EXPERIENCE
    2020 – 2024  |  Backend Engineer  |  TechCorp Inc.
    - Designed and deployed microservices serving 1M+ requests/day.
    - Led migration from monolith to Docker-based microservices.

    2018 – 2020  |  Junior Developer  |  Startify Ltd.
    - Developed internal tools with Django and React.

    EDUCATION
    2014 – 2018  |  B.Tech Computer Science  |  NIT Trichy  |  CGPA 8.7/10

    CERTIFICATIONS
    - AWS Certified Solutions Architect (2022)
    - Google Professional Data Engineer (2023)

    PROJECTS
    SmartResume AI – Built an NLP-based resume screening tool using BERT embeddings.
    DataPipeline – Created an ETL pipeline processing 500K records/day using Apache Kafka.
""").strip()

JOB_DESC = textwrap.dedent("""
    We are looking for a Senior Backend Engineer with strong experience in:
    Python, FastAPI, Docker, PostgreSQL and Redis.
    REST API design and microservices. At least 3 years of professional experience.
    Bonus: Machine learning experience, AWS certifications.
""").strip()


def run_test(name, fn):
    try:
        result = fn()
        results.append((PASS, name, str(result)[:120]))
        print(f"{PASS} {name}")
        return result
    except Exception as e:
        import traceback
        results.append((FAIL, name, str(e)))
        print(f"{FAIL} {name}  →  {e}")
        traceback.print_exc()
        return None


# ─── 1. Resume Parser ────────────────────────────────────────────────────────
def test_parser():
    from app.ai.parser.resume_parser import ResumeParser
    parser = ResumeParser()
    # Uses .parse() method
    parsed = parser.parse(SAMPLE_RESUME)
    assert "skills" in parsed and len(parsed["skills"]) > 0, f"No skills extracted. Got: {parsed}"
    assert parsed["experience_years"] >= 0, "experience_years missing"
    return f"skills={parsed['skills'][:3]}, exp_years={parsed['experience_years']}"

run_test("ResumeParser.parse()", test_parser)


# ─── 2. Embedder ────────────────────────────────────────────────────────────
def test_embedder():
    from app.ai.embeddings.embedder import EmbeddingEngine
    emb = EmbeddingEngine()
    vec = emb.embed_text(SAMPLE_RESUME[:500])
    assert len(vec) > 0, "Empty embedding"
    sim = EmbeddingEngine.cosine_similarity(vec, emb.embed_text(JOB_DESC))
    assert 0.0 <= sim <= 1.0, f"Similarity out of range: {sim}"
    return f"dim={len(vec)}, similarity={sim:.4f}"

run_test("EmbeddingEngine.embed_text() + cosine_similarity()", test_embedder)


# ─── 3. Semantic Matcher ─────────────────────────────────────────────────────
def test_matcher():
    from app.ai.embeddings.embedder import EmbeddingEngine
    from app.ai.semantic_match.matcher import SemanticMatcher
    emb = EmbeddingEngine()
    matcher = SemanticMatcher(emb)
    score = matcher.match(SAMPLE_RESUME, JOB_DESC)
    assert 0.0 <= score <= 1.0, f"Score out of range: {score}"
    return f"semantic_match={score:.4f}"

run_test("SemanticMatcher.match()", test_matcher)


# ─── 4. XGBoost Ranker ──────────────────────────────────────────────────────
def test_ranker():
    from app.ai.ranking.xgboost_ranker import XGBoostRanker
    ranker = XGBoostRanker()
    candidates = [{
        "features": {
            "semantic_similarity": 0.82,
            "skill_overlap": 0.70,
            "experience_years": 5,
            "education_score": 0.9,
            "projects_score": 0.75,
            "certifications_score": 0.8,
        },
        "raw_text": "dummy"
    }]
    ranked = ranker.rank(candidates)
    assert len(ranked) == 1, "Ranked list length mismatch"
    assert "rank_score" in ranked[0], "Missing rank_score"
    score = ranked[0]["rank_score"]
    assert 0.0 <= score <= 1.0, f"Score out of range: {score}"
    return f"rank_score={score:.4f}"

run_test("XGBoostRanker.rank()", test_ranker)


# ─── 5. SHAP Explainer ──────────────────────────────────────────────────────
def test_shap():
    from app.ai.explainability.shap_explainer import SHAPExplainer
    explainer = SHAPExplainer()
    candidate = {
        "features": {
            "semantic_similarity": 0.82,
            "skill_overlap": 0.70,
            "experience_years": 5,
            "education_score": 0.9,
            "projects_score": 0.75,
            "certifications_score": 0.8,
        },
        "parsed_resume": {"skills": ["Python", "FastAPI"]},
    }
    explanation = explainer.explain(candidate, JOB_DESC)
    assert "positive_features" in explanation, "Missing positive_features"
    assert "shap_values" in explanation, "Missing shap_values"
    return f"top_pos={explanation['positive_features'][:1]}"

run_test("SHAPExplainer.explain()", test_shap)


# ─── 6. Resume Summarizer ───────────────────────────────────────────────────
def test_summarizer():
    from app.ai.summarizer.resume_summarizer import ResumeSummarizer
    summarizer = ResumeSummarizer()
    candidate = {
        "raw_text": SAMPLE_RESUME,
        "parsed_resume": {
            "name": "John Doe",
            "skills": ["Python", "FastAPI", "Docker"],
            "experience_years": 5,
            "education": ["B.Tech Computer Science"],
        },
        "features": {"semantic_similarity": 0.82},
    }
    result = summarizer.summarize(candidate)
    assert "summary" in result and len(result["summary"]) > 10, f"Empty summary: {result}"
    return result["summary"][:100]

run_test("ResumeSummarizer.summarize()", test_summarizer)


# ─── 7. Fraud Detector ──────────────────────────────────────────────────────
def test_fraud():
    from app.ai.fraud_detection.fraud_detector import FraudDetector
    detector = FraudDetector()
    candidate = {
        "raw_text": SAMPLE_RESUME,
        "parsed_resume": {
            "skills": ["Python", "FastAPI"],
            "experience_years": 5,
            "education": ["B.Tech Computer Science"],
        }
    }
    result = detector.detect(candidate)
    assert "risk_score" in result, f"Missing risk_score. Got keys: {list(result.keys())}"
    assert 0.0 <= result["risk_score"] <= 1.0, f"Score out of range: {result['risk_score']}"
    return f"risk_score={result['risk_score']:.2f}, warnings={result.get('warnings', [])[:2]}"

run_test("FraudDetector.detect()", test_fraud)


# ─── 8. Bias Detector ───────────────────────────────────────────────────────
def test_bias():
    from app.ai.bias_detection.bias_detector import BiasDetector
    detector = BiasDetector()
    candidate = {
        "raw_text": SAMPLE_RESUME,
        "parsed_resume": {"name": "John Doe", "skills": ["Python"]},
    }
    result = detector.analyze(candidate)
    assert "bias_score" in result or "anonymized_text" in result, f"Missing expected keys. Got: {result.keys()}"
    return f"keys={list(result.keys())}"

run_test("BiasDetector.analyze()", test_bias)


# ─── 9. Recommender ─────────────────────────────────────────────────────────
def test_recommender():
    from app.ai.recommendation.recommender import RecommendationEngine
    rec = RecommendationEngine()
    candidates = [{
        "raw_text": SAMPLE_RESUME,
        "job_description": JOB_DESC,
        "parsed_resume": {
            "skills": ["Python", "FastAPI", "Docker"],
        },
        "rank_score": 0.82,
    }]
    result = rec.recommend(candidates, limit=1)
    assert len(result) == 1, "Recommender returned no results"
    assert "recommendations" in result[0], f"Missing 'recommendations'. Got: {result[0].keys()}"
    recs = result[0]["recommendations"]
    assert "missing_skills" in recs, "Missing 'missing_skills'"
    return f"missing={recs['missing_skills'][:2]}, courses={len(recs.get('courses', []))}"

run_test("RecommendationEngine.recommend()", test_recommender)


# ─── 10. FAISS Vector Store ──────────────────────────────────────────────────
def test_faiss():
    from app.ai.vector_db.faiss_store import FAISSStore
    from app.ai.embeddings.embedder import EmbeddingEngine
    emb = EmbeddingEngine()
    store = FAISSStore()
    vec = emb.embed_text(SAMPLE_RESUME[:500])
    store.add(vec, metadata={"id": 999, "name": "John Doe Test"})
    results_list = store.search(vec, top_k=1)
    assert len(results_list) >= 1, "FAISS search returned no results"
    # store.search returns [(score, meta), ...]
    score, meta = results_list[0]
    return f"found={meta.get('name', '?')}, score={score:.4f}"

run_test("FAISSStore.add() + search()", test_faiss)


# ─── 11. Full AIService Pipeline ────────────────────────────────────────────
def test_ai_service():
    from app.services.ai_service import AIService
    service = AIService()
    result = service.score_candidate(SAMPLE_RESUME, JOB_DESC)
    assert "parsed_resume" in result, f"Missing 'parsed_resume'. Keys: {list(result.keys())}"
    assert "summary" in result, f"Missing 'summary'. Keys: {list(result.keys())}"
    assert "explanation" in result, f"Missing 'explanation'. Keys: {list(result.keys())}"
    assert "fraud_report" in result, f"Missing 'fraud_report'. Keys: {list(result.keys())}"
    assert "bias_report" in result, f"Missing 'bias_report'. Keys: {list(result.keys())}"
    features = result.get("features", {})
    assert "semantic_similarity" in features, f"Missing semantic_similarity in features: {list(features.keys())}"
    assert "skill_overlap" in features, f"Missing skill_overlap in features: {list(features.keys())}"
    return (f"summary_len={len(result.get('summary', {}).get('summary', ''))}, "
            f"sim={features.get('semantic_similarity', 0):.4f}, "
            f"skill_overlap={features.get('skill_overlap', 0):.2f}")

run_test("AIService.score_candidate() [Full Pipeline]", test_ai_service)


# ─── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == PASS)
total = len(results)
print(f"Result: {passed}/{total} tests passed\n")
for icon, name, detail in results:
    status = "PASS" if icon == PASS else "FAIL"
    print(f"  [{status}] {name}")
    if icon == FAIL:
        print(f"         → {detail}")

if passed < total:
    sys.exit(1)
